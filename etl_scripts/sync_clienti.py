# File: etl_scripts/sync_clienti.py

import os
import sys
import pandas as pd
import pyodbc
from sqlalchemy import create_engine
from dotenv import load_dotenv
import logging

# Configurazione del Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Caricamento delle Variabili d'Ambiente
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dotenv_path = os.path.join(project_root, '.env')
if not os.path.exists(dotenv_path):
    logging.error(f"File .env non trovato in {dotenv_path}.")
    sys.exit(1)
load_dotenv(dotenv_path=dotenv_path)

# Lettura delle configurazioni per i database
DB2_SYSTEM = os.environ.get('DB2_SYSTEM')
DB2_USER = os.environ.get('DB2_USER')
DB2_PASSWORD = os.environ.get('DB2_PASSWORD')
DB2_DRIVER_NAME = os.environ.get('DB2_DRIVER_NAME')
MYSQL_CONN_STR = os.environ.get('DATABASE_URL')
DB2_LIBS = os.environ.get('DB2_LIBS')

if not all([DB2_SYSTEM, DB2_USER, DB2_PASSWORD, DB2_DRIVER_NAME, MYSQL_CONN_STR]):
    logging.error("Una o più variabili d'ambiente essenziali non sono impostate nel .env.")
    sys.exit(1)

# Costruzione della stringa di connessione DSN-less per DB2
DB2_CONN_STR = (
    f"DRIVER={{{DB2_DRIVER_NAME}}};"
    f"SYSTEM={DB2_SYSTEM};"
    f"UID={DB2_USER};"
    f"PWD={DB2_PASSWORD};"
)
if DB2_LIBS:
    DB2_CONN_STR += f"DBQ=, {DB2_LIBS};"


def sync_anagrafica_clienti():
    """
    Estrae l'anagrafica clienti da DB2 e la carica su MySQL, sostituendo i dati esistenti.
    """
    logging.info("--- AVVIO SCRIPT SYNC ANAGRAFICA CLIENTI ---")

    # 1. EXTRACT: Esecuzione della query su DB2
    query_db2 = """
    SELECT
        FCODCL, FCODAG, FCOCON, CLISIDA.CCOCODV, FCATCL, FRAGCL,
        FINDCL, FLOCCL, FCAPCL, FPROCL, FTE1CL, FTE2CL, FCESCL,
        FVENCL, FCODDK, FBLXSC, TABSCADGG.tcam14 AS GGSCAD
    FROM CISEUROF.FANAGCLI
    INNER JOIN CISEUROF.FCONVCLI AS CLISIDA ON (CLISIDA.CCOCODN = CISEUROF.FANAGCLI.FCODCL)
    LEFT JOIN CISEUROF.FTABELLE AS TABSCADGG ON (TRIM(TABSCADGG.TCODTA) = fcodas AND TABSCADGG.TKEYTA = 'TABASSOC')
    """

    df = None
    try:
        logging.info(f"Connessione a DB2 (SYSTEM: {DB2_SYSTEM})...")
        with pyodbc.connect(DB2_CONN_STR) as db2_conn:
            logging.info("Esecuzione query su DB2 per anagrafica clienti...")
            df = pd.read_sql(query_db2, db2_conn)
        logging.info(f"Estratti {len(df)} record da DB2.")
    except Exception as e:
        logging.error(f"Errore durante l'estrazione da DB2: {e}")
        return

    if df.empty:
        logging.warning("Nessun dato estratto da DB2. Lo script termina.")
        return

    # 2. TRANSFORM: Rinomina le colonne
    logging.info("Trasformazione dei dati (rinomina colonne)...")
    column_mapping = {
        'FCODCL': 'codice', 'FCODAG': 'codice_agente', 'FCOCON': 'codice_contabile',
        'CCOCODV': 'codice_soggetto_sdi', 'FCATCL': 'categoria', 'FRAGCL': 'ragione_sociale',
        'FINDCL': 'indirizzo', 'FLOCCL': 'localita', 'FCAPCL': 'cap', 'FPROCL': 'provincia',
        'FTE1CL': 'telefono1', 'FTE2CL': 'telefono2', 'FCESCL': 'cessato',
        'FVENCL': 'vendita', 'FCODDK': 'codice_dk', 'FBLXSC': 'blocco_sconti',
        'GGSCAD': 'giorni_scadenza'
    }
    df.rename(columns=column_mapping, inplace=True)

    # Pulisce eventuali spazi bianchi extra che possono arrivare da DB2
    df['cessato'] = df['cessato'].astype(str).str.strip()
    df['vendita'] = df['vendita'].astype(str).str.strip()
    df['blocco_sconti'] = df['blocco_sconti'].astype(str).str.strip()

    # 3. LOAD: Caricamento su MySQL
    try:
        logging.info(f"Connessione a MySQL e caricamento di {len(df)} record...")
        engine = create_engine(MYSQL_CONN_STR)
        df.to_sql('cliente', con=engine, if_exists='replace', index=False)
        logging.info("Caricamento della tabella 'cliente' completato con successo.")
    except Exception as e:
        logging.error(f"Errore durante il caricamento su MySQL: {e}")
        return

    logging.info("--- SCRIPT COMPLETATO CON SUCCESSO ---")


if __name__ == "__main__":
    sync_anagrafica_clienti()