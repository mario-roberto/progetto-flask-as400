# File: app/main/routes.py
from flask import render_template
from flask_login import login_required
from app.main import bp # Creeremo main/bp in main/__init__.py

@bp.route('/')
@bp.route('/index')
@login_required # Questa pagina richiede che l'utente sia loggato!
def index():
    # Qui in futuro interrogheremo il DB2 o MySQL per le statistiche
    return render_template('index.html', title='Dashboard')