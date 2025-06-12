# File: app/main/__init__.py (CORRETTO)
from flask import Blueprint

bp = Blueprint('main', __name__)

from app.main import routes  # <-- Importato ALLA FINE, dopo la definizione di bp