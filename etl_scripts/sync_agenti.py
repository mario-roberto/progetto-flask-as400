# File: etl_scripts/sync_agenti.py

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
    logging.error(f"File .env non trovato in {dotenv_path}. Lo script non può continuare.")
    sys.exit(1)

load_dotenv(dotenv_path=dotenv_path)

# --- Lettura delle configurazioni per i database ---
DB2_SYSTEM = os.environ.get('DB2_SYSTEM')
DB2_USER = os.environ.get('DB2_USER')
DB2_PASSWORD = os.environ.get('DB2_PASSWORD')
DB2_DRIVER_NAME = os.environ.get('DB2_DRIVER_NAME')
MYSQL_CONN_STR = os.environ.get('DATABASE_URL')

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

def sync_anagrafica_agenti():
    """
    Estrae l'anagrafica agenti da DB2 e la carica su MySQL, sostituendo i dati esistenti.
    """
    logging.info("--- AVVIO SCRIPT SYNC ANAGRAFICA AGENTI ---")

    # 1. EXTRACT: Esecuzione della query su DB2
    query_db2 = "SELECT * FROM CISEUROF.FANAGAGE"

    df = None
    try:
        logging.info(f"Connessione a DB2 (SYSTEM: {DB2_SYSTEM})...")
        with pyodbc.connect(DB2_CONN_STR) as db2_conn:
            logging.info("Esecuzione query su DB2 per anagrafica agenti...")
            df = pd.read_sql(query_db2, db2_conn)
        logging.info(f"Estratti {len(df)} record da DB2.")
    except Exception as e:
        logging.error(f"Errore durante l'estrazione da DB2: {e}")
        return

    if df.empty:
        logging.warning("Nessun dato estratto da DB2. Lo script termina.")
        return

    # 2. TRANSFORM: Rinomina le colonne e converte i tipi
    logging.info("Trasformazione dei dati...")
    # I nomi delle colonne in AS/400 sono già maiuscoli, Pandas li manterrà.
    # Li convertiamo in minuscolo per coerenza.
    df.columns = [col.lower() for col in df.columns]

    column_mapping = {
        'agecod': 'codice', 'agersc': 'ragione_sociale', 'agepre': 'prenotazione',
        'agetel': 'telefono', 'agefax': 'fax', 'ageprc': 'percentuale_provvigione',
        'agecel': 'cellulare', 'agevdt': 'data_variazione', 'agevdi': 'inizio_validita',
        'agecom': 'note_commerciali', 'agencv': 'note_contabili', 'agecap': 'cap',
        'ageind': 'indirizzo', 'ageloc': 'localita', 'agepro': 'provincia',
        'agezon': 'zona', 'agebp1': 'bp1', 'agebp2': 'bp2', 'agebp3': 'bp3',
        'agebp4': 'bp4', 'agebp5': 'bp5', 'agebl1': 'bl1', 'agebl2': 'bl2',
        'agebl3': 'bl3', 'agebl4': 'bl4', 'agebl5': 'bl5', 'agebu1': 'bu1',
        'agebu2': 'bu2', 'agebu3': 'bu3', 'agebu4': 'bu4', 'agebu5': 'bu5',
        'ageprp': 'provvigione_prodotto', 'ageprl': 'provvigione_linea',
        'ageli1': 'li1', 'ageli2': 'li2', 'ageli3': 'li3', 'ageli4': 'li4',
        'ageli5': 'li5', 'ageli6': 'li6'
    }
    df.rename(columns=column_mapping, inplace=True)

    # Converte le date (in AS400 potrebbero essere numeri tipo 20240612)
    # Se il formato è diverso, adatta la direttiva 'format'
    df['data_variazione'] = pd.to_datetime(df['data_variazione'], errors='coerce', format='%Y%m%d')
    df['inizio_validita'] = pd.to_datetime(df['inizio_validita'], errors='coerce', format='%Y%m%d')

    # 3. LOAD: Caricamento su MySQL
    try:
        logging.info(f"Connessione a MySQL e caricamento di {len(df)} record...")
        engine = create_engine(MYSQL_CONN_STR)
        df.to_sql('agente', con=engine, if_exists='replace', index=False)
        logging.info("Caricamento della tabella 'agente' completato con successo.")
    except Exception as e:
        logging.error(f"Errore durante il caricamento su MySQL: {e}")
        return

    logging.info("--- SCRIPT COMPLETATO CON SUCCESSO ---")


if __name__ == "__main__":
    sync_anagrafica_agenti()