# File: app/__init__.py
from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager



# Inizializza le estensioni
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'  # Dice a Flask-Login qual è la pagina di login
login_manager.login_message = 'Effettua il login per accedere a questa pagina.'


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Collega le estensioni all'app
    db.init_app(app)
    login_manager.init_app(app)

    # Importa e registra i Blueprint
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    # Importa i modelli per essere sicuri che SQLAlchemy li veda
    from app import models

    return app