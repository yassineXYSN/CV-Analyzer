# utils.py
from sqlalchemy.orm import Session
from databasehr.models import AdminCompanyAccess

def add_user_to_company(
    db: Session, 
    company_id: int, 
    admin_id: int, 
    access_level: str = 'admin', 
    granted_by: int = None
):
    """Ajoute un administrateur à une entreprise (sans commit)"""
    new_access = AdminCompanyAccess(
        admin_id=admin_id,
        company_id=company_id,
        access_level=access_level,
        granted_by=granted_by
    )
    db.add(new_access)
    return new_access  # Retourne l'objet sans commiter