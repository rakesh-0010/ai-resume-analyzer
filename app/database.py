import logging
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text, create_engine

logger = logging.getLogger(__name__)
db = SQLAlchemy()


def init_db(app):
    """
    Initializes the database with the Flask app.
    Tests primary database (e.g. MySQL) availability before registering.
    If MySQL is not reachable or not running locally, smoothly defaults to SQLite fallback.
    """
    db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')

    if db_uri.startswith('mysql'):
        try:
            # Quick connectivity probe with a short timeout
            test_engine = create_engine(db_uri, connect_args={'connect_timeout': 2})
            with test_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            test_engine.dispose()
            logger.info("Successfully connected to MySQL database: %s", db_uri)
        except Exception as e:
            logger.warning(
                "MySQL database connection test failed (%s). "
                "Falling back to local SQLite database (%s) for immediate execution.",
                e, app.config.get('SQLITE_FALLBACK_URI')
            )
            app.config['SQLALCHEMY_DATABASE_URI'] = app.config.get('SQLITE_FALLBACK_URI')

    db.init_app(app)

    with app.app_context():
        try:
            # Explicitly import models so tables are registered in SQLAlchemy metadata before create_all
            import app.models  # noqa: F401
            db.create_all()
            logger.info("Successfully created database tables: %s", list(db.metadata.tables.keys()))
        except Exception as ex:
            logger.error("Error creating database tables: %s", ex)
