import bcrypt
from passlib.context import CryptContext

# Configuration pour le hachage des mots de passe
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hache un mot de passe"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie un mot de passe"""
    return pwd_context.verify(plain_password, hashed_password)

def create_admin_user(email: str, password: str, first_name: str, last_name: str, role: str = "hr_admin"):
    """Crée un nouvel utilisateur admin avec mot de passe haché"""
    from database import SessionLocal
    import models
    
    db = SessionLocal()
    try:
        # Vérifier si l'utilisateur existe déjà
        existing_user = db.query(models.HRAdmin).filter(models.HRAdmin.email == email).first()
        if existing_user:
            print(f"❌ L'utilisateur {email} existe déjà!")
            return None
        
        # Hacher le mot de passe
        hashed_password = hash_password(password)
        
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
        return None
    finally:
        db.close()

# Fonction pour tester la connexion
def test_login(email: str, password: str):
    """Teste la connexion d'un utilisateur"""
    from database import SessionLocal
    import models
    
    db = SessionLocal()
    try:
        user = db.query(models.HRAdmin).filter(models.HRAdmin.email == email).first()
        if not user:
            print(f"❌ Utilisateur {email} non trouvé!")
            return False
        
        if verify_password(password, user.password_hash):
            print(f"✅ Connexion réussie pour {email}!")
            return True
        else:
            print(f"❌ Mot de passe incorrect pour {email}!")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        return False
    finally:
        db.close()
