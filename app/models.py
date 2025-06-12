# File: app/models.py
from sqlalchemy import Index
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


# File: app/models.py
# ... (le classi User, VendutoMensile, etc. rimangono) ...

class Articolo(db.Model):
    __tablename__ = 'articolo'

    # Chiave primaria
    codice = db.Column(db.String(20), primary_key=True)

    # Campi di ricerca comuni - aggiungiamo un indice
    descrizione = db.Column(db.String(255), index=True)
    codice_fornitore = db.Column(db.String(20), index=True)

    # Altri campi
    stato = db.Column(db.String(10))
    descrizione_fornitore = db.Column(db.String(100))
    legame = db.Column(db.String(20))

    # Gerarchie merceologiche - indicizziamo i codici
    codice_ambito = db.Column(db.String(10), index=True)
    descrizione_ambito = db.Column(db.String(100))
    codice_settore = db.Column(db.String(10), index=True)
    descrizione_settore = db.Column(db.String(100))
    codice_reparto = db.Column(db.String(10), index=True)
    descrizione_reparto = db.Column(db.String(100))
    codice_famiglia = db.Column(db.String(10), index=True)
    descrizione_famiglia = db.Column(db.String(100))
    codice_sottofamiglia = db.Column(db.String(10), index=True)
    descrizione_sottofamiglia = db.Column(db.String(100))

    unita_misura = db.Column(db.String(5))
    pezzi_per_collo = db.Column(db.Integer)

    # Usiamo DECIMAL per prezzi e valori monetari per evitare errori di arrotondamento
    iva = db.Column(db.Numeric(5, 2))  # Es: 22.00
    prezzo_fornitore = db.Column(db.Numeric(10, 4))  # Es: 123456.7890
    prezzo_scontrino = db.Column(db.Numeric(10, 2))

    codice_rep_cassa = db.Column(db.Integer, index=True)
    descrizione_rep_cassa = db.Column(db.String(100))

    giacenza = db.Column(db.Numeric(10, 3))
    data_inserimento = db.Column(db.Date)

    def __repr__(self):
        return f'<Articolo {self.codice} - {self.descrizione}>'

    # Opzionale: Creazione di indici composti se fai spesso ricerche su più colonne insieme
    # Esempio: se cerchi spesso per settore E reparto insieme
    # __table_args__ = (
    #     Index('idx_settore_reparto', 'codice_settore', 'codice_reparto'),
    # )py


class Agente(db.Model):
    __tablename__ = 'agente'

    codice = db.Column(db.Integer, primary_key=True)  # AGECOD
    ragione_sociale = db.Column(db.String(100), index=True)  # AGERSC
    prenotazione = db.Column(db.String(50))  # AGEPRE
    telefono = db.Column(db.String(20))  # AGETEL
    fax = db.Column(db.String(20))  # AGEFAX
    percentuale_provvigione = db.Column(db.Numeric(5, 2))  # AGEPRC
    cellulare = db.Column(db.String(20))  # AGECEL
    data_variazione = db.Column(db.Date)  # AGEVDT
    inizio_validita = db.Column(db.Date)  # AGEVDI
    note_commerciali = db.Column(db.Text)  # AGECOM
    note_contabili = db.Column(db.Text)  # AGENCV

    # Indirizzo
    cap = db.Column(db.String(10))  # AGECAP
    indirizzo = db.Column(db.String(100))  # AGEIND
    localita = db.Column(db.String(100))  # AGELOC
    provincia = db.Column(db.String(2), index=True)  # AGEPRO
    zona = db.Column(db.String(10), index=True)  # AGEZON

    # Campi BP (potrebbero essere importi o percentuali)
    bp1 = db.Column(db.Numeric(12, 2))  # AGEBP1
    bp2 = db.Column(db.Numeric(12, 2))  # AGEBP2
    bp3 = db.Column(db.Numeric(12, 2))  # AGEBP3
    bp4 = db.Column(db.Numeric(12, 2))  # AGEBP4
    bp5 = db.Column(db.Numeric(12, 2))  # AGEBP5

    # Campi BL
    bl1 = db.Column(db.Numeric(12, 2))  # AGEBL1
    bl2 = db.Column(db.Numeric(12, 2))  # AGEBL2
    bl3 = db.Column(db.Numeric(12, 2))  # AGEBL3
    bl4 = db.Column(db.Numeric(12, 2))  # AGEBL4
    bl5 = db.Column(db.Numeric(12, 2))  # AGEBL5

    # Campi BU
    bu1 = db.Column(db.Numeric(12, 2))  # AGEBU1
    bu2 = db.Column(db.Numeric(12, 2))  # AGEBU2
    bu3 = db.Column(db.Numeric(12, 2))  # AGEBU3
    bu4 = db.Column(db.Numeric(12, 2))  # AGEBU4
    bu5 = db.Column(db.Numeric(12, 2))  # AGEBU5

    # Provvigioni (presumo)
    provvigione_prodotto = db.Column(db.Numeric(5, 2))  # AGEPRP
    provvigione_linea = db.Column(db.Numeric(5, 2))  # AGEPRL

    # Campi LI
    li1 = db.Column(db.Numeric(12, 2))  # AGELI1
    li2 = db.Column(db.Numeric(12, 2))  # AGELI2
    li3 = db.Column(db.Numeric(12, 2))  # AGELI3
    li4 = db.Column(db.Numeric(12, 2))  # AGELI4
    li5 = db.Column(db.Numeric(12, 2))  # AGELI5
    li6 = db.Column(db.Numeric(12, 2))  # AGELI6

    def __repr__(self):
        return f'<Agente {self.codice} - {self.ragione_sociale}>'


class Cliente(db.Model):
    __tablename__ = 'cliente'

    codice = db.Column(db.Integer, primary_key=True)  # FCODCL
    codice_agente = db.Column(db.Integer, index=True)  # FCODAG
    codice_contabile = db.Column(db.Integer)  # FCOCON
    codice_soggetto_sdi = db.Column(db.String(20))  # CLISIDA.CCOCODV
    categoria = db.Column(db.String(10), index=True)  # FCATCL
    ragione_sociale = db.Column(db.String(100), index=True)  # FRAGCL

    # Indirizzo
    indirizzo = db.Column(db.String(100))  # FINDCL
    localita = db.Column(db.String(100))  # FLOCCL
    cap = db.Column(db.String(10))  # FCAPCL
    provincia = db.Column(db.String(2), index=True)  # FPROCL

    # Contatti
    telefono1 = db.Column(db.String(20))  # FTE1CL
    telefono2 = db.Column(db.String(20))  # FTE2CL

    # Condizioni commerciali
    cessato = db.Column(db.String(1))  # FCESCL (probabilmente 'S'/'N')
    vendita = db.Column(db.String(1))  # FVENCL
    codice_dk = db.Column(db.String(10))  # FCODDK
    blocco_sconti = db.Column(db.String(1))  # FBLXSC
    giorni_scadenza = db.Column(db.Integer)  # GGSCAD

    def __repr__(self):
        return f'<Cliente {self.codice} - {self.ragione_sociale}>'


class Vendita(db.Model):
    __tablename__ = 'vendita'

    # Chiave primaria composita non è gestita elegantemente da to_sql con replace,
    # quindi usiamo un id auto-incrementante per semplicità e performance.
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Informazioni di testata
    codice_magazzino = db.Column(db.BigInteger)  # TCOMAG
    tipo_movimento = db.Column(db.String(5))  # TTIPMO
    codice_soggetto_sdi = db.Column(db.String(20), index=True)  # CCOCODV
    numero_registrazione = db.Column(db.BigInteger, index=True)  # TNUMRE
    listino_scelto = db.Column(db.String(5))  # TLISCE - Sembra una stringa dai dati ('1A')
    listino_vendita = db.Column(db.String(5))  # TLISVE - Sembra una stringa dai dati ('1V')
    data_documento = db.Column(db.Date, index=True, nullable=False)  # DATADOC
    numero_documento = db.Column(db.BigInteger)  # TNUMDO
    lettera_documento = db.Column(db.String(5))  # TLETDO
    codice_agente = db.Column(db.Integer, index=True)  # TCODAG
    provvigione_agente = db.Column(db.Numeric(5, 2))  # TPROAG
    totale_merce = db.Column(db.Numeric(12, 2))  # TTOTME
    totale_documento = db.Column(db.Numeric(12, 2))  # TTOTDO

    # Informazioni di dettaglio
    codice_articolo = db.Column(db.String(20), index=True)  # DCOART
    descrizione_articolo = db.Column(db.String(255))  # DDEART
    pezzi_spediti = db.Column(db.Integer)  # DPEZSP
    pezzi_cespiti = db.Column(db.Integer)  # DCESSP
    prezzo_vendita = db.Column(db.Numeric(12, 4))  # DVENSP
    aliquota_iva = db.Column(db.Numeric(5, 2))  # DALIVA

    # Indici composti per query analitiche comuni
    __table_args__ = (
        Index('idx_vendita_articolo_data', 'codice_articolo', 'data_documento'),
        Index('idx_vendita_agente_data', 'codice_agente', 'data_documento'),
    )

    def __repr__(self):
        return f'<Vendita {self.numero_registrazione} - Art. {self.codice_articolo}>'


class SyncControl(db.Model):
    __tablename__ = 'sync_control'

    script_name = db.Column(db.String(50), primary_key=True)
    last_sync_date = db.Column(db.Date, nullable=False)

    def __repr__(self):
        return f'<SyncControl {self.script_name}: {self.last_sync_date}>'