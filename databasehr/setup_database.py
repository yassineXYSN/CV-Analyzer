#!/usr/bin/env python3
"""
Script pour configurer la base de données
"""

import os
import sys
from pathlib import Path

def create_env_file():
    """Créer le fichier .env s'il n'existe pas"""
    if not os.path.exists('.env'):
        print("📝 Création du fichier .env...")
        
        # Demander les informations de base de données
        print("\n🗄️  Configuration de la base de données:")
        db_host = input("Host (localhost): ").strip() or "localhost"
        db_port = input("Port (3306): ").strip() or "3306"
        db_user = input("Utilisateur (root): ").strip() or "root"
        db_password = input("Mot de passe: ").strip()
        db_name = input("Nom de la base (cv_analyzer_pro): ").strip() or "cv_analyzer_pro"
        
        # Générer une clé secrète
        import secrets
        secret_key = secrets.token_urlsafe(32)
        
        # Créer le contenu du fichier .env
        env_content = f"""# Configuration de la base de données
DATABASE_HOST={db_host}
DATABASE_PORT={db_port}
DATABASE_USER={db_user}
DATABASE_PASSWORD={db_password}
DATABASE_NAME={db_name}

# Clé secrète pour l'application
SECRET_KEY={secret_key}

# Configuration optionnelle
DEBUG=True
ENVIRONMENT=development
"""
        
        with open('.env', 'w') as f:
            f.write(env_content)
        
        print("✅ Fichier .env créé")
        return True
    else:
        print("✅ Fichier .env existe déjà")
        return True

def test_mysql_connection():
    """Tester la connexion MySQL"""
    try:
        import pymysql
        from dotenv import load_dotenv
        
        load_dotenv()
        
        connection = pymysql.connect(
            host=os.getenv("DATABASE_HOST", "localhost"),
            port=int(os.getenv("DATABASE_PORT", "3306")),
            user=os.getenv("DATABASE_USER", "root"),
            password=os.getenv("DATABASE_PASSWORD", ""),
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            print(f"✅ MySQL connecté - Version: {version[0]}")
        
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ Erreur de connexion MySQL: {e}")
        return False

def create_database():
    """Créer la base de données si elle n'existe pas"""
    try:
        import pymysql
        from dotenv import load_dotenv
        
        load_dotenv()
        
        db_name = os.getenv("DATABASE_NAME", "cv_analyzer_pro")
        
        connection = pymysql.connect(
            host=os.getenv("DATABASE_HOST", "localhost"),
            port=int(os.getenv("DATABASE_PORT", "3306")),
            user=os.getenv("DATABASE_USER", "root"),
            password=os.getenv("DATABASE_PASSWORD", ""),
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            # Vérifier si la base existe
            cursor.execute(f"SHOW DATABASES LIKE '{db_name}'")
            if cursor.fetchone():
                print(f"✅ Base de données '{db_name}' existe déjà")
            else:
                # Créer la base de données
                cursor.execute(f"CREATE DATABASE {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                print(f"✅ Base de données '{db_name}' créée")
        
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la création de la base: {e}")
        return False

def setup_tables():
    """Configurer les tables"""
    try:
        from databasehr.database import init_database
        return init_database()
    except Exception as e:
        print(f"❌ Erreur lors de la création des tables: {e}")
        return False

def main():
    """Configuration complète de la base de données"""
    print("🔧 Configuration de la base de données CV Analyzer Pro")
    print("=" * 60)
    
    # Étape 1: Créer le fichier .env
    print("\n1. Configuration des variables d'environnement...")
    if not create_env_file():
        sys.exit(1)
    
    # Étape 2: Tester la connexion MySQL
    print("\n2. Test de connexion MySQL...")
    if not test_mysql_connection():
        print("\n💡 Vérifiez que MySQL/MariaDB est démarré et accessible")
        sys.exit(1)
    
    # Étape 3: Créer la base de données
    print("\n3. Création de la base de données...")
    if not create_database():
        sys.exit(1)
    
    # Étape 4: Créer les tables
    print("\n4. Création des tables...")
    if not setup_tables():
        sys.exit(1)
    
    print(f"\n{'=' * 60}")
    print("✅ Configuration terminée avec succès !")
    print("\n🚀 Vous pouvez maintenant démarrer le serveur:")
    print("   python start_server.py")

if __name__ == "__main__":
    main()
