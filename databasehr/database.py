import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration de la base de données
DATABASE_HOST = os.getenv("DATABASE_HOST", "localhost")
DATABASE_PORT = os.getenv("DATABASE_PORT", "3306")
DATABASE_USER = os.getenv("DATABASE_USER", "root")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD", "")
DATABASE_NAME = os.getenv("DATABASE_NAME", "cv_analyzer_pro")

# Construction de l'URL de connexion
SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"

# Affichage sécurisé de la configuration (sans mot de passe)
safe_url = SQLALCHEMY_DATABASE_URL.replace(f":{DATABASE_PASSWORD}@", ":****@") if DATABASE_PASSWORD else SQLALCHEMY_DATABASE_URL
print(f"🗄️  Connexion DB: {safe_url}")

# Création du moteur SQLAlchemy
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=False  # Mettre à True pour voir les requêtes SQL
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base pour les modèles
Base = declarative_base()

# Fonction utilitaire pour obtenir une session DB
def get_db():
    """Générateur de session de base de données"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Test de connexion
def test_connection():
    """Teste la connexion à la base de données"""
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        print("✅ Connexion à la base de données réussie")
        return True
    except Exception as e:
        print(f"❌ Erreur de connexion à la base de données: {e}")
        return False

# Initialisation des tables
def init_database():
    """Initialise la base de données et crée les tables"""
    try:
        import databasehr.models as models
        print("🔧 Création des tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ Tables créées avec succès")
        return True
    except Exception as e:
        print(f"❌ Erreur lors de la création des tables: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Test de la configuration de base de données")
    print("=" * 50)
    
    if test_connection():
        if init_database():
            print("✅ Base de données prête à l'emploi")
        else:
            print("❌ Problème lors de l'initialisation")
    else:
        print("❌ Impossible de se connecter à la base de données")
        print("\n💡 Vérifiez:")
        print("   • Que MySQL/MariaDB est démarré")
        print("   • Les paramètres de connexion dans .env")
        print("   • Que la base de données existe")
