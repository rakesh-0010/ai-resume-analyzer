import logging
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

logger = logging.getLogger(__name__)
db = SQLAlchemy()


def init_db(app):
    """
    Initializes the database with the Flask app.
    Tries MySQL connection first. If unreachable or not yet created,
    falls back cleanly to SQLite for seamless local execution.
    """
    db.init_app(app)

    with app.app_context():
        try:
            # Test connection
            db.session.execute(text("SELECT 1"))
            db.create_all()
            logger.info("Successfully connected to primary database: %s", app.config['SQLALCHEMY_DATABASE_URI'])
        except OperationalError as e:
            logger.warning(
                "Primary database (%s) connection failed: %s. Switching to SQLite fallback.",
                app.config['SQLALCHEMY_DATABASE_URI'], e
            )
            # Reconfigure engine to SQLite fallback
            app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLITE_FALLBACK_URI']
            db.engine.dispose()
            db.init_app(app)
            db.create_all()
            logger.info("Created tables on fallback SQLite database: %s", app.config['SQLITE_FALLBACK_URI'])
        except Exception as ex:
            logger.error("Database initialization error: %s", ex)
            # Create all tables on whatever engine is active
            db.create_all()
