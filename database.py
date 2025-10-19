import os
from urllib.parse import quote_plus
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

"""Build a robust SQLAlchemy MySQL URL from environment variables.

Handles missing or unset values gracefully and avoids inserting literal
"None" into the URL (which breaks SQLAlchemy's port parsing).
"""

# Read database credentials from environment
DB_USER = (os.getenv("DB_USER") or "root").strip()
DB_PASSWORD_RAW = os.getenv("DB_PASSWORD")
DB_PASSWORD = quote_plus(DB_PASSWORD_RAW) if DB_PASSWORD_RAW is not None else ""
DB_HOST = (os.getenv("DB_HOST") or "localhost").strip()
DB_NAME = (os.getenv("DB_NAME") or "cv_analyzer_pro").strip()
DB_PORT_RAW = (os.getenv("DB_PORT") or "").strip()

# Include port only if provided and numeric
PORT_SEGMENT = f":{DB_PORT_RAW}" if DB_PORT_RAW.isdigit() else ""

# Build the connection URL
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}{PORT_SEGMENT}/{DB_NAME}"

# Create the engine
engine = create_engine(DATABASE_URL)

# Create a session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base for models
Base = declarative_base()

# Optional: test connection
try:
    conn = engine.connect()
    print("SUCCESS: Connected to MySQL")
except Exception as e:
    print("ERROR: Could not connect to MySQL:", e)
