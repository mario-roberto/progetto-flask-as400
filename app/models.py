# File: app/models.py
from app import db, login_manager
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

# Questa funzione è richiesta da Flask-Login per sapere come caricare un utente
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    role = db.Column(db.String(20), nullable=False, default='user') # 'user' o 'admin'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

# --- MODELLI PER STATISTICHE (Esempi da definire meglio in seguito) ---
# Questo è solo un esempio basato sul menu che hai mostrato.
# Lo definiremo meglio quando mi darai i dettagli.
class VendutoMensile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    anno = db.Column(db.Integer, index=True)
    mese = db.Column(db.Integer, index=True)
    importo_totale = db.Column(db.Float)
    # ... altre colonne come fornitore_id, agente_id etc.