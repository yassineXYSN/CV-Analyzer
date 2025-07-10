from database import SessionLocal
import models
from datetime import datetime
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

def create_company(user_id: int, company_data: dict):
    """Créer une nouvelle entreprise et l'associer à un utilisateur"""
    print(f"🏢 COMPANY_UTILS: Création entreprise pour user {user_id}")
    print(f"📋 COMPANY_UTILS: Données reçues: {company_data}")
    
    db = SessionLocal()
    try:
        # Nettoyer les données pour éviter les valeurs None problématiques
        clean_data = {}
        for key, value in company_data.items():
            if value is not None:
                clean_data[key] = value
        
        print(f"🧹 COMPANY_UTILS: Données nettoyées: {clean_data}")
        
        # Créer l'entreprise avec les données nettoyées
        new_company = models.Company(
            company_name=clean_data.get('company_name'),
            industry=clean_data.get('industry'),
            company_size=clean_data.get('company_size'),
            founded_year=clean_data.get('founded_year'),
            description=clean_data.get('description'),
            address=clean_data.get('address'),
            phone=clean_data.get('phone'),
            email=clean_data.get('email'),
            website=clean_data.get('website'),
            linkedin_url=clean_data.get('linkedin_url'),
            twitter_url=clean_data.get('twitter_url'),
            facebook_url=clean_data.get('facebook_url'),
            setup_completed=True,
            created_by=user_id
        )
        
        db.add(new_company)
        db.commit()
        db.refresh(new_company)
        
        print(f"✅ COMPANY_UTILS: Entreprise créée avec ID: {new_company.id}")
        
        # Créer l'accès admin pour l'utilisateur
        admin_access = models.AdminCompanyAccess(
            admin_id=user_id,
            company_id=new_company.id,
            access_level='owner',
            granted_by=user_id
        )
        
        db.add(admin_access)
        db.commit()
        
        print(f"✅ COMPANY_UTILS: Accès admin créé pour user {user_id}")
        
        return new_company.id
        
    except Exception as e:
        db.rollback()
        print(f"❌ COMPANY_UTILS: Erreur création entreprise: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        db.close()

def update_company(company_id: int, company_data: dict):
    """Mettre à jour une entreprise existante"""
    print(f"📝 COMPANY_UTILS: Mise à jour entreprise ID: {company_id}")
    print(f"📋 COMPANY_UTILS: Données reçues: {company_data}")
    
    db = SessionLocal()
    try:
        company = db.query(models.Company).filter(models.Company.id == company_id).first()
        
        if not company:
            print(f"❌ COMPANY_UTILS: Entreprise {company_id} non trouvée")
            return False
        
        # Mettre à jour les champs
        for key, value in company_data.items():
            if hasattr(company, key):
                setattr(company, key, value)
        
        company.setup_completed = True
        company.updated_at = datetime.now()
        
        db.commit()
        print(f"✅ COMPANY_UTILS: Entreprise {company_id} mise à jour")
        return True
        
    except Exception as e:
        db.rollback()
        print(f"❌ COMPANY_UTILS: Erreur mise à jour entreprise: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

def get_user_company(user_id: int):
    """Récupérer l'entreprise d'un utilisateur"""
    print(f"🔍 COMPANY_UTILS: Recherche entreprise pour user {user_id}")
    
    db = SessionLocal()
    try:
        # Chercher l'accès de l'utilisateur à une entreprise
        access = db.query(models.AdminCompanyAccess).filter(
            models.AdminCompanyAccess.admin_id == user_id
        ).first()
        
        if not access:
            print(f"❌ COMPANY_UTILS: Aucun accès entreprise trouvé pour user {user_id}")
            return None
        
        # Récupérer l'entreprise
        company = db.query(models.Company).filter(
            models.Company.id == access.company_id
        ).first()
        
        if company:
            print(f"✅ COMPANY_UTILS: Entreprise trouvée: {company.company_name}")
        else:
            print(f"❌ COMPANY_UTILS: Entreprise non trouvée pour ID: {access.company_id}")
        
        return company
        
    except Exception as e:
        print(f"❌ COMPANY_UTILS: Erreur récupération entreprise: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        db.close()

def get_company_admins(company_id: int):
    """Récupérer les administrateurs d'une entreprise"""
    print(f"👥 COMPANY_UTILS: Recherche admins pour entreprise {company_id}")
    
    db = SessionLocal()
    try:
        # Récupérer les accès à l'entreprise
        accesses = db.query(models.AdminCompanyAccess).filter(
            models.AdminCompanyAccess.company_id == company_id
        ).all()
        
        admins = []
        for access in accesses:
            admin = db.query(models.HRAdmin).filter(
                models.HRAdmin.id == access.admin_id
            ).first()
            
            if admin:
                admins.append({
                    'id': admin.id,
                    'email': admin.email,
                    'first_name': admin.first_name,
                    'last_name': admin.last_name,
                    'role': admin.role,
                    'access_level': access.access_level,
                    'is_active': admin.is_active,
                    'last_login': admin.last_login,
                    'granted_at': access.granted_at
                })
        
        print(f"✅ COMPANY_UTILS: {len(admins)} admins trouvés")
        return admins
        
    except Exception as e:
        print(f"❌ COMPANY_UTILS: Erreur récupération admins: {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        db.close()

def add_user_to_company(company_id: int, admin_id: int, access_level: str = 'admin', granted_by: int = None):
    """Ajouter un utilisateur à une entreprise"""
    print(f"➕ COMPANY_UTILS: Ajout user {admin_id} à entreprise {company_id}")
    
    db = SessionLocal()
    try:
        # Vérifier si l'accès existe déjà
        existing_access = db.query(models.AdminCompanyAccess).filter(
            models.AdminCompanyAccess.admin_id == admin_id,
            models.AdminCompanyAccess.company_id == company_id
        ).first()
        
        if existing_access:
            print(f"⚠️ COMPANY_UTILS: Accès existe déjà")
            return True, "Accès existe déjà"
        
        # Créer l'accès
        new_access = models.AdminCompanyAccess(
            admin_id=admin_id,
            company_id=company_id,
            access_level=access_level,
            granted_by=granted_by
        )
        
        db.add(new_access)
        db.commit()
        
        print(f"✅ COMPANY_UTILS: Accès créé avec succès")
        return True, "Accès créé avec succès"
        
    except Exception as e:
        db.rollback()
        print(f"❌ COMPANY_UTILS: Erreur création accès: {e}")
        import traceback
        traceback.print_exc()
        return False, f"Erreur: {str(e)}"
    finally:
        db.close()
        
# company_utils.py
from database import SessionLocal
from models import AdminCompanyAccess, Company

def get_user_company(user_id: int):
    db = SessionLocal()
    try:
        # Trouver l'accès de l'admin à une entreprise
        access = db.query(AdminCompanyAccess).filter(
            AdminCompanyAccess.admin_id == user_id
        ).first()
        
        if not access:
            return None
        
        # Récupérer l'entreprise associée
        company = db.query(Company).filter(
            Company.id == access.company_id
        ).first()
        
        return company
    finally:
        db.close()