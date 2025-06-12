# File: config.py
import os
from dotenv import load_dotenv

# Carica le variabili dal file .env
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '../.env'))  # Il .env è nella cartella superiore rispetto a app/


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')

    # Configurazione per SQLAlchemy e MySQL
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Configurazione per DB2 (la useremo direttamente con pyodbc)
    DB2_CONNECTION_STRING = (
        f"DSN={os.environ.get('DB2_DSN')};"
        f"UID={os.environ.get('DB2_USER')};"
        f"PWD={os.environ.get('DB2_PASSWORD')};"
    )
    DEBUG = os.environ.get('FLASK_DEBUG') == '1'