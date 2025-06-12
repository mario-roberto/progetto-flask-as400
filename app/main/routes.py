# File: app/main/routes.py
from flask import render_template, request, flash, redirect, url_for, abort
from flask_login import login_required, current_user
from app.main import bp
from app.models import User
from app import db

@bp.route('/')
@bp.route('/index')
@login_required
def index():
    return render_template('index.html', title='Dashboard')

# --- NUOVA ROTTA PER GESTIONE UTENTI ---
@bp.route('/users', methods=['GET', 'POST'])
@login_required
def users():
    # 1. Sicurezza: solo gli admin possono accedere a questa pagina
    if current_user.role != 'admin':
        abort(403)  # Errore "Forbidden"

    # 2. Logica per la creazione di un nuovo utente (quando il form viene inviato)
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')

        # Controlla se l'utente o l'email esistono già
        if User.query.filter_by(username=username).first():
            flash('Username già in uso.', 'danger')
        elif User.query.filter_by(email=email).first():
            flash('Email già in uso.', 'danger')
        else:
            # Crea il nuovo utente
            new_user = User(username=username, email=email, role=role)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            flash('Nuovo utente creato con successo!', 'success')
            return redirect(url_for('main.users'))

    # 3. Logica per visualizzare la pagina (richiesta GET)
    all_users = User.query.all()
    return render_template('users.html', title='Gestione Utenti', users=all_users)


# --- NUOVA ROTTA PER MODIFICARE UN UTENTE ---
@bp.route('/user/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_user(id):
    if current_user.role != 'admin':
        abort(403)  # Solo gli admin possono modificare

    user_to_edit = User.query.get_or_404(id)  # Trova l'utente o restituisci errore 404

    if request.method == 'POST':
        # Recupera i dati dal form
        username = request.form.get('username')
        email = request.form.get('email')
        role = request.form.get('role')
        password = request.form.get('password')

        # Controlla se il nuovo username o email sono già in uso da ALTRI utenti
        if User.query.filter(User.id != id).filter_by(username=username).first():
            flash('Username già in uso da un altro utente.', 'danger')
        elif User.query.filter(User.id != id).filter_by(email=email).first():
            flash('Email già in uso da un altro utente.', 'danger')
        else:
            # Aggiorna i dati dell'utente
            user_to_edit.username = username
            user_to_edit.email = email
            user_to_edit.role = role
            # Aggiorna la password solo se è stata inserita
            if password:
                user_to_edit.set_password(password)

            db.session.commit()
            flash('Utente aggiornato con successo!', 'success')
            return redirect(url_for('main.users'))

    # Se la richiesta è GET, mostra la pagina con i dati pre-compilati
    return render_template('edit_user.html', title='Modifica Utente', user=user_to_edit)


# --- NUOVA ROTTA PER ELIMINARE UN UTENTE ---
@bp.route('/user/delete/<int:id>', methods=['POST'])
@login_required
def delete_user(id):
    if current_user.role != 'admin':
        abort(403)  # Solo gli admin possono eliminare

    # Non permettere a un admin di eliminare sé stesso
    if id == current_user.id:
        flash('Non puoi eliminare il tuo stesso account!', 'danger')
        return redirect(url_for('main.users'))

    user_to_delete = User.query.get_or_404(id)
    db.session.delete(user_to_delete)
    db.session.commit()
    flash('Utente eliminato con successo.', 'success')
    return redirect(url_for('main.users'))