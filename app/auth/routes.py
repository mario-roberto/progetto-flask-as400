# File: app/auth/routes.py
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user
from app import db
from app.auth import bp  # Creeremo auth/bp in auth/__init__.py
from app.models import User


# Aggiungeremo un form qui in futuro

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user is None or not user.check_password(password):
            flash('Username o password non validi')
            return redirect(url_for('auth.login'))
        login_user(user)
        return redirect(url_for('main.index'))

    return render_template('auth/login.html', title='Sign In')


@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))