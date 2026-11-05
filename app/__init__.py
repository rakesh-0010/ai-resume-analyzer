import os
import json
from flask import Flask, render_template
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

from config import Config
from app.database import db, init_db

login_manager = LoginManager()
csrf = CSRFProtect()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure upload and reports folders exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['REPORT_FOLDER'], exist_ok=True)

    # Initialize extensions
    init_db(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'
    
    csrf.init_app(app)

    # Custom Jinja2 Filters
    @app.template_filter('score_badge')
    def score_badge_filter(score):
        try:
            val = float(score)
            if val >= 80:
                return 'badge-success'
            elif val >= 60:
                return 'badge-warning'
            return 'badge-danger'
        except (ValueError, TypeError):
            return 'badge-secondary'

    @app.template_filter('from_json')
    def from_json_filter(val):
        try:
            return json.loads(val) if val else []
        except Exception:
            return []

    # User loader for Flask-Login
    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    from app.auth import auth_bp
    from app.routes import main_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    # Error Handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('500.html'), 500

    return app
