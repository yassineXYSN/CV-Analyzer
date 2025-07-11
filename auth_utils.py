"""
Utilitaires d'authentification - Version finale corrigée
"""

import hashlib
import secrets
import hmac
from databasehr.database import SessionLocal
import databasehr.models as models

# Gestionnaire de mots de passe sécurisé sans bcrypt
class PasswordManager:
    """Gestionnaire de mots de passe avec PBKDF2"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hache un mot de passe avec salt"""
        # Générer un salt aléatoire de 32 bytes
        salt = secrets.token_hex(32)
        
        # Hacher le mot de passe avec PBKDF2
        pwd_hash = hashlib.pbkdf2_hmac(
            'sha256', 
            password.encode('utf-8'), 
            salt.encode('utf-8'), 
            100000  # 100,000 itérations
        )
        
        # Retourner salt:hash
        return f"{salt}:{pwd_hash.hex()}"
    
    @staticmethod
    def verify_password(password: str, stored_hash: str) -> bool:
        """Vérifie un mot de passe"""
        try:
            # Séparer le salt et le hash
            if ':' not in stored_hash:
                return False
                
            salt, pwd_hash = stored_hash.split(':', 1)
            
            # Recalculer le hash avec le même salt
            new_hash = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode('utf-8'),
                salt.encode('utf-8'),
                100000
            )
            
            # Comparer de manière sécurisée
            return hmac.compare_digest(pwd_hash, new_hash.hex())
            
        except Exception as e:
            print(f"Erreur vérification mot de passe: {e}")
            return False

# Utiliser le gestionnaire sécurisé
password_manager = PasswordManager()

def hash_password(password: str) -> str:
    """Hache un mot de passe"""
    return password_manager.hash_password(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie un mot de passe"""
    return password_manager.verify_password(plain_password, hashed_password)

def create_admin_user(email: str, password: str, first_name: str, last_name: str, role: str = "hr_admin"):
    """Crée un nouvel utilisateur admin avec mot de passe haché"""
    db = SessionLocal()
    try:
        # Vérifier si l'utilisateur existe déjà
        existing_user = db.query(models.HRAdmin).filter(models.HRAdmin.email == email).first()
        if existing_user:
            print(f"❌ L'utilisateur {email} existe déjà!")
            return None
        
        # Hacher le mot de passe
        hashed_password = hash_password(password)
        print(f"🔐 Hash créé pour {email}: {hashed_password[:50]}...")
        
        # Créer le nouvel admin
        new_admin = models.HRAdmin(
            email=email,
            password_hash=hashed_password,
            first_name=first_name,
            last_name=last_name,
            role=role,
            is_active=True
        )
        
        db.add(new_admin)
        db.commit()
        db.refresh(new_admin)
        
        print(f"✅ Utilisateur {email} créé avec succès!")
        return new_admin.id
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erreur lors de la création: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        db.close()

def test_login(email: str, password: str):
    """Teste la connexion d'un utilisateur"""
    db = SessionLocal()
    try:
        user = db.query(models.HRAdmin).filter(models.HRAdmin.email == email).first()
        if not user:
            print(f"❌ Utilisateur {email} non trouvé!")
            return False
        
        print(f"🔍 Test pour {email}")
        print(f"   Hash stocké: {user.password_hash[:50]}...")
        print(f"   Mot de passe testé: {password}")
        
        if verify_password(password, user.password_hash):
            print(f"✅ Connexion réussie pour {email}!")
            return True
        else:
            print(f"❌ Mot de passe incorrect pour {email}!")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

def authenticate_user(email: str, password: str):
    """Authentifie un utilisateur et retourne ses informations"""
    db = SessionLocal()
    try:
        user = db.query(models.HRAdmin).filter(models.HRAdmin.email == email).first()
        
        if not user:
            return None
        
        if not user.is_active:
            return None
        
        if verify_password(password, user.password_hash):
            return {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role
            }
        
        return None
        
    except Exception as e:
        print(f"❌ Erreur authentification: {e}")
        return None
    finally:
        db.close()
