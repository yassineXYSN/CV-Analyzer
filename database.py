from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Configuration MySQL (via XAMPP)
DATABASE_URL = "mysql+pymysql://root:@localhost/cv_analyzer_pro"

# Création de l'engine
engine = create_engine(DATABASE_URL)

# Session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base pour déclarer les modèles
Base = declarative_base()

engine = create_engine("mysql+pymysql://root:@localhost/cv_analyzer_pro")
conn = engine.connect()
print("✅ Connexion réussie à MySQL")