import os
import logging

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

# Create the SQLAlchemy database instance
db = SQLAlchemy(model_class=Base)

def init_db(app):
    """Initialize the database with the Flask app"""
    # Configure the database, relative to the app instance folder
    # Check if DATABASE_URL is available, if not use SQLite as fallback
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        logger.warning("DATABASE_URL not found, falling back to SQLite database")
        db_url = "sqlite:///air_quality.db"

    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    logger.info(f"Using database: {db_url.split('@')[-1] if '@' in db_url else db_url}")

    # Initialize the app with the extension
    db.init_app(app)

    # Create database tables
    with app.app_context():
        # Import models here to avoid circular imports
        from backend.models import User, AQIData, CountryAQI, CityAQI
        
        # Create all tables if they don't exist
        db.create_all()
