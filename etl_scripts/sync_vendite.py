# File: etl_scripts/sync_vendite.py

import os
import sys
import pandas as pd
import pyodbc
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import logging
from datetime import date, timedelta

# --- Configurazione ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
SCRIPT_NAME = 'sync_vendite'
START_DATE = date(2023, 1, 1)
DAYS_CHUNK = 30  # Numero di giorni da elaborare per ogni esecuzione

# --- Caricamento Variabili d'Ambiente e Connessioni ---
# (Codice identico agli altri script, lo includo per completezza)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dotenv_path = os.path.join(project_root, '.env')
if not os.path.exists(dotenv_path):
    logging.error(f"File .env non trovato in {dotenv_path}.")
    sys.exit(1)
load_dotenv(dotenv_path=dotenv_path)

DB2_SYSTEM = os.environ.get('DB2_SYSTEM')
DB2_USER = os.environ.get('DB2_USER')
DB2_PASSWORD = os.environ.get('DB2_PASSWORD')
DB2_DRIVER_NAME = os.environ.get('DB2_DRIVER_NAME')
MYSQL_CONN_STR = os.environ.get('DATABASE_URL')
DB2_LIBS = os.environ.get('DB2_LIBS')

if not all([DB2_SYSTEM, DB2_USER, DB2_PASSWORD, DB2_DRIVER_NAME, MYSQL_CONN_STR]):
    logging.error("Una o più variabili d'ambiente essenziali non sono impostate nel .env.")
    sys.exit(1)

DB2_CONN_STR = (f"DRIVER={{{DB2_DRIVER_NAME}}};SYSTEM={DB2_SYSTEM};UID={DB2_USER};PWD={DB2_PASSWORD};")
if DB2_LIBS: DB2_CONN_STR += f"DBQ=, {DB2_LIBS};"


# --- Fine Configurazione ---

def get_last_sync_date(engine):
    """Legge l'ultima data sincronizzata dal database di controllo."""
    with engine.connect() as conn:
        result = conn.execute(
            text(f"SELECT last_sync_date FROM sync_control WHERE script_name = '{SCRIPT_NAME}'")).scalar_one_or_none()
        if result:
            return result
        # Se non c'è nessuna riga, partiamo dal giorno prima della data di inizio
        return START_DATE - timedelta(days=1)


def update_last_sync_date(engine, new_date):
    """Aggiorna l'ultima data sincronizzata nel database di controllo."""
    with engine.connect() as conn:
        # Usa un "upsert": UPDATE se esiste, INSERT se non esiste.
        # La sintassi può variare leggermente tra versioni di MySQL. Questa è la più comune.
        stmt = text(
            f"INSERT INTO sync_control (script_name, last_sync_date) "
            f"VALUES ('{SCRIPT_NAME}', '{new_date.strftime('%Y-%m-%d')}') "
            f"ON DUPLICATE KEY UPDATE last_sync_date = VALUES(last_sync_date);"
        )
        conn.execute(stmt)
        conn.commit()


def sync_documenti_vendita():
    logging.info(f"--- AVVIO SCRIPT {SCRIPT_NAME.upper()} ---")
    engine_mysql = create_engine(MYSQL_CONN_STR)

    # 1. Determina il prossimo intervallo di date da elaborare
    last_date = get_last_sync_date(engine_mysql)
    start_chunk_date = last_date + timedelta(days=1)
    end_chunk_date = start_chunk_date + timedelta(days=DAYS_CHUNK - 1)

    # Non andare oltre il giorno precedente a oggi
    yesterday = date.today() - timedelta(days=1)
    if end_chunk_date > yesterday:
        end_chunk_date = yesterday

    if start_chunk_date > yesterday:
        logging.info("Dati già sincronizzati fino a ieri. Nessuna nuova elaborazione necessaria.")
        return

    logging.info(
        f"Elaborazione del periodo dal {start_chunk_date.strftime('%Y-%m-%d')} al {end_chunk_date.strftime('%Y-%m-%d')}")

    # Converti le date nel formato numerico YYYYMMDD per la query DB2
    start_date_db2 = int(start_chunk_date.strftime('%Y%m%d'))
    end_date_db2 = int(end_chunk_date.strftime('%Y%m%d'))

    # 2. EXTRACT: Esegui la query per il chunk di date corrente
    query_db2 = f"""
    SELECT
        TCOMAG, TTIPMO, CCOCODV, TNUMRE, TLISCE, TLISVE, FDAT8i as DATADOC,
        TNUMDO, TLETDO, TCODAG, TPROAG, TTOTME, TTOTDO, DCOART, DDEART,
        DPEZSP, DCESSP, DVENSP, DALIVA
    FROM CISEUROF.FMOVITES, CISEUROF.FMOVIDET, CISEUROO.FSETTIMA, CISEUROF.LCONVCLI
    WHERE DNUMRE = TNUMRE AND TCOINT = CCOCODN
      AND TDATDO = FDAT5G AND TINTER = 'C' AND TFLAG = ''
      AND DFLAG = '' AND DPEZSP > 0
      AND FDAT8i BETWEEN {start_date_db2} AND {end_date_db2}
    """

    df = None
    try:
        logging.info(f"Connessione a DB2...")
        with pyodbc.connect(DB2_CONN_STR) as db2_conn:
            df = pd.read_sql(query_db2, db2_conn)
        logging.info(f"Estratti {len(df)} record da DB2 per il periodo corrente.")
    except Exception as e:
        logging.error(f"Errore durante l'estrazione da DB2: {e}")
        return

    if df.empty:
        logging.info("Nessun nuovo record trovato nel periodo. Aggiorno la data di controllo e termino.")
        update_last_sync_date(engine_mysql, end_chunk_date)
        return

    # 3. TRANSFORM
    logging.info("Trasformazione dei dati...")
    df.columns = [col.lower() for col in df.columns]
    column_mapping = {
        'tcomag': 'codice_magazzino', 'ttipmo': 'tipo_movimento', 'ccocodv': 'codice_soggetto_sdi',
        'tnumre': 'numero_registrazione', 'tlisce': 'listino_scelto', 'tlisve': 'listino_vendita',
        'datadoc': 'data_documento', 'tnumdo': 'numero_documento', 'tletdo': 'lettera_documento',
        'tcodag': 'codice_agente', 'tproag': 'provvigione_agente', 'ttotme': 'totale_merce',
        'ttotdo': 'totale_documento', 'dcoart': 'codice_articolo', 'ddeart': 'descrizione_articolo',
        'dpezsp': 'pezzi_spediti', 'dcessp': 'pezzi_cespiti', 'dvensp': 'prezzo_vendita',
        'daliva': 'aliquota_iva'
    }
    df.rename(columns=column_mapping, inplace=True)
    df['data_documento'] = pd.to_datetime(df['data_documento'], format='%Y%m%d', errors='coerce')
    df['codice_articolo'] = pd.to_numeric(df['codice_articolo'], errors='coerce').fillna(0).astype('int64')

    # 4. LOAD (in modalità APPEND)
    try:
        logging.info(f"Caricamento di {len(df)} record in modalità 'append' su MySQL...")
        df.to_sql('vendita', con=engine_mysql, if_exists='append', index=False)
        logging.info("Caricamento completato.")

        # 5. AGGIORNA STATO
        # Se tutto è andato a buon fine, aggiorna l'ultima data sincronizzata
        update_last_sync_date(engine_mysql, end_chunk_date)
        logging.info(f"Data di sincronizzazione aggiornata a {end_chunk_date.strftime('%Y-%m-%d')}.")

    except Exception as e:
        logging.error(f"Errore durante il caricamento su MySQL: {e}. La data di controllo non è stata aggiornata.")
        return

    logging.info(f"--- SCRIPT {SCRIPT_NAME.upper()} COMPLETATO CON SUCCESSO ---")


if __name__ == "__main__":
    sync_documenti_vendita()