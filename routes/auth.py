from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from app import db

auth = Blueprint('auth', __name__, url_prefix='/auth')

@auth.route('/login', methods=['GET', 'POST'])
def login():
    """登录页面"""
    # Import models here to ensure Flask app context is available
    from models import User

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember', False)

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            # Validate redirect URL to prevent open redirect attacks
            if next_page and not next_page.startswith('/'):
                next_page = None
            if next_page and '//' in next_page:
                next_page = None
            return redirect(next_page if next_page else '/')
        else:
            flash('Invalid username or password', 'error')

    return render_template('login.html')

@auth.route('/logout')
@login_required
def logout():
    """登出"""
    logout_user()
    return redirect(url_for('auth.login'))
