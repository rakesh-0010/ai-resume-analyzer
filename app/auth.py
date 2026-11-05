from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app.database import db
from app.models import User
from app.forms import LoginForm, RegisterForm, ProfileForm
from app.demo_seeder import seed_demo_accounts

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/demo/candidate')
def demo_candidate_login():
    """1-Click direct login as Demo Candidate with pre-loaded resumes and ATS analysis."""
    seed_demo_accounts(current_app)
    user = User.query.filter_by(email='demo.candidate@ats-pro.ai').first()
    if user:
        login_user(user)
        flash('⚡ Signed in as Demo Candidate! Explore your pre-analyzed resume, ATS score gauge, and job match results.', 'success')
        return redirect(url_for('routes.dashboard'))
    flash('Could not initialize demo candidate account.', 'danger')
    return redirect(url_for('auth.login'))


@auth_bp.route('/demo/admin')
def demo_admin_login():
    """1-Click direct login as Demo Administrator with platform telemetry access."""
    seed_demo_accounts(current_app)
    admin = User.query.filter_by(email='demo.admin@ats-pro.ai').first()
    if admin:
        login_user(admin)
        flash('🛡️ Signed in as Demo Administrator! You have access to user management, metrics, and administration.', 'info')
        return redirect(url_for('routes.admin_dashboard'))
    flash('Could not initialize demo administrator account.', 'danger')
    return redirect(url_for('auth.login'))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('routes.dashboard'))

    form = RegisterForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if existing_user:
            flash('An account with this email already exists. Please log in.', 'warning')
            return redirect(url_for('auth.login'))

        # Check if first user; make admin
        user_count = User.query.count()
        role = 'admin' if user_count == 0 else 'user'

        user = User(
            name=form.name.data.strip(),
            email=form.email.data.lower().strip(),
            role=role
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash('Account created successfully! Welcome to your AI Resume Analyzer dashboard.', 'success')
        return redirect(url_for('routes.dashboard'))

    return render_template('register.html', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('routes.dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            flash(f'Welcome back, {user.name}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('routes.dashboard'))
        else:
            flash('Invalid email or password. Please verify your credentials.', 'danger')

    return render_template('login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been securely signed out.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        current_user.name = form.name.data.strip()
        current_user.phone = form.phone.data.strip() if form.phone.data else None
        current_user.target_role = form.target_role.data.strip() if form.target_role.data else None
        current_user.bio = form.bio.data.strip() if form.bio.data else None

        if form.new_password.data:
            current_user.set_password(form.new_password.data)
            flash('Profile and password updated successfully!', 'success')
        else:
            flash('Profile updated successfully!', 'success')

        db.session.commit()
        return redirect(url_for('auth.profile'))

    return render_template('profile.html', form=form, user=current_user)
