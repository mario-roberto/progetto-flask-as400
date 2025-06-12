# File: etl_scripts/sync_articoli.py

import os
import sys
import pandas as pd
import pyodbc
from sqlalchemy import create_engine
from dotenv import load_dotenv
import logging

# Configurazione del Logging per un output chiaro
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Caricamento delle Variabili d'Ambiente dal file .env alla radice del progetto
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dotenv_path = os.path.join(project_root, '.env')

if not os.path.exists(dotenv_path):
    logging.error(f"File .env non trovato in {dotenv_path}. Lo script non può continuare.")
    sys.exit(1)

load_dotenv(dotenv_path=dotenv_path)

# --- Lettura delle configurazioni per i database ---
DB2_SYSTEM = os.environ.get('DB2_SYSTEM')
DB2_USER = os.environ.get('DB2_USER')
DB2_PASSWORD = os.environ.get('DB2_PASSWORD')
DB2_LIBS = os.environ.get('DB2_LIBS')
DB2_DRIVER_NAME = os.environ.get('DB2_DRIVER_NAME')  # Leggiamo il nome del driver
MYSQL_CONN_STR = os.environ.get('DATABASE_URL')

# Controllo di validità delle configurazioni
if not all([DB2_SYSTEM, DB2_USER, DB2_PASSWORD, DB2_DRIVER_NAME, MYSQL_CONN_STR]):
    logging.error("Una o più variabili d'ambiente essenziali non sono impostate nel file .env. Controlla DB2_SYSTEM, DB2_USER, DB2_PASSWORD, DB2_DRIVER_NAME, DATABASE_URL.")
    sys.exit(1)

# Costruzione dinamica della stringa di connessione DSN-less per DB2
try:
    DB2_CONN_STR = (
        f"DRIVER={{{DB2_DRIVER_NAME}}};"  # Usa le doppie graffe per l'escape del nome driver
        f"SYSTEM={DB2_SYSTEM};"
        f"UID={DB2_USER};"
        f"PWD={DB2_PASSWORD};"
    )
    if DB2_LIBS:
        DB2_CONN_STR += f"DBQ=, {DB2_LIBS};"
except Exception as e:
    logging.error(f"Errore nella costruzione della stringa di connessione: {e}")
    sys.exit(1)


def sync_anagrafica_articoli():
    """
    Funzione principale per estrarre da DB2, trasformare e caricare su MySQL.
    """
    logging.info("--- AVVIO SCRIPT SYNC ANAGRAFICA ARTICOLI ---")

    # 1. EXTRACT: Esecuzione della query su DB2 AS/400
    query_db2 = """
    SELECT DISTINCT
        FCOART, FDESAG, FDSTAT, FFORNI, FFORSC, FLEGAM, AMBITO.TCODTA AS CODAMBITO,
        AMBITO.TDESCO AS DESAMBITO, SETTORE.TCODTA as CODSETTORE, SETTORE.TDESCO as DESCSETTORE,
        COMP.FDCODI as CODCOMP, COMP.FDDESC as DESCOMP, FAM.FSCODI as CODFAM,
        FAM.FSDESC as DESFAM, SUBFAM.FGCODI as COD_SUBFAM, SUBFAM.FGDESC as DESSFAM,
        FUNMIS, FMPLCU, TABALIVA.TCAM16 as IVA, FMPLPF, FMPLSF, FREPCA,
        REPCA.TDESCO as DESREPCA, GIACART.GIACENZA/FMPLCU as GIACENZA, a.FDAT8I
    FROM CISEUROF.FSITART0
    LEFT JOIN (
        select GCOART,SUM(GTGIPZ) AS GIACENZA from CISEUROF.FMOVIGIA
        where GMAGAZ>=90000 AND(GMAGAZ,GCOART,GDATAG) IN (
            select GMAGAZ,GCOART,MAX (GDATAG) as GDATAG from CISEUROF.FMOVIGIA
            group by GMAGAZ,GCOART
        ) GROUP BY GCOART
    ) as GIACART on( GIACART.GCOART = CISEUROF.FSITART0.FCOART),
    CISEUROF.FDIPARTM as COMP, CISEUROF.FSUPARTM as FAM, CISEUROF.FGRPARTM as SUBFAM,
    CISEUROF.FTABELLE as SETTORE, CISEUROF.FFORNIMC, CISEUROF.FTABELLE as TABALIVA,
    CISEUROF.FTABELLE as REPCA, CISEUROF.FTABELLE as AMBITO, ciseuroo.fsettima AS a
    WHERE FCOGRM = SUBFAM.FGCODI
      AND SUBFAM.FSBDLE = FAM.FSCODI AND SUBFAM.FDIPLE = COMP.FDCODI
      AND COMP.FDSETT = SETTORE.TCODTA AND SETTORE.TKEYTA = 'SETTMERC'
      AND FFORNI = FFOCOD AND TABALIVA.TKEYTA = 'TABALIVA'
      AND TABALIVA.TCODTA = FIDIVA AND REPCA.TKEYTA = 'TABREPCA'
      AND cast(REPCA.TCODTA as int) = FREPCA AND TABALIVA.TKEYTA = 'TABALIVA'
      AND AMBITO.TKEYTA = 'TABFASAR' AND AMBITO.TCODTA = FCOFAS
      AND a.FDAT5G = FDATAI
    ORDER BY SETTORE.TDESCO , COMP.FDDESC, FAM.FSDESC, SUBFAM.FGDESC, FDESAG
    """

    df = None
    try:
        logging.info(f"Connessione a DB2 (SYSTEM: {DB2_SYSTEM}) usando il driver '{DB2_DRIVER_NAME}'...")
        with pyodbc.connect(DB2_CONN_STR) as db2_conn:
            logging.info("Esecuzione query su DB2. Potrebbe richiedere tempo...")
            df = pd.read_sql(query_db2, db2_conn)
        logging.info(f"Estratti {len(df)} record da DB2.")
    except Exception as e:
        logging.error(f"Errore durante l'estrazione da DB2: {e}")
        return

    if df.empty:
        logging.warning("Nessun dato estratto da DB2. Lo script termina.")
        return

    # 2. TRANSFORM: Rinominare le colonne
    logging.info("Trasformazione dei dati (rinomina colonne e gestione tipi)...")
    column_mapping = {
        'FCOART': 'codice', 'FDESAG': 'descrizione', 'FDSTAT': 'stato', 'FFORNI': 'codice_fornitore',
        'FFORSC': 'descrizione_fornitore', 'FLEGAM': 'legame', 'CODAMBITO': 'codice_ambito',
        'DESAMBITO': 'descrizione_ambito', 'CODSETTORE': 'codice_settore', 'DESCSETTORE': 'descrizione_settore',
        'CODCOMP': 'codice_reparto', 'DESCOMP': 'descrizione_reparto', 'CODFAM': 'codice_famiglia',
        'DESFAM': 'descrizione_famiglia', 'COD_SUBFAM': 'codice_sottofamiglia', 'DESSFAM': 'descrizione_sottofamiglia',
        'FUNMIS': 'unita_misura', 'FMPLCU': 'pezzi_per_collo', 'IVA': 'iva', 'FMPLPF': 'prezzo_fornitore',
        'FMPLSF': 'prezzo_scontrino', 'FREPCA': 'codice_rep_cassa', 'DESREPCA': 'descrizione_rep_cassa',
        'GIACENZA': 'giacenza', 'FDAT8I': 'data_inserimento'
    }
    df.rename(columns=column_mapping, inplace=True)
    df['data_inserimento'] = pd.to_datetime(df['data_inserimento'], errors='coerce')
    df['giacenza'].fillna(0, inplace=True)

    # 3. LOAD: Caricamento su MySQL
    try:
        logging.info(f"Connessione a MySQL e caricamento di {len(df)} record...")
        engine = create_engine(MYSQL_CONN_STR)
        df.to_sql('articolo', con=engine, if_exists='replace', index=False)
        logging.info("Caricamento su MySQL completato con successo.")
    except Exception as e:
        logging.error(f"Errore durante il caricamento su MySQL: {e}")
        return

    logging.info("--- SCRIPT COMPLETATO CON SUCCESSO ---")


if __name__ == "__main__":
    sync_anagrafica_articoli()