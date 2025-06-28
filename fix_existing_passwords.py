#!/usr/bin/env python3
"""
Script pour corriger les mots de passe existants qui ne sont pas hachés correctement
"""

from auth_utils import hash_password
from database import SessionLocal
import models

def fix_demo_passwords():
    """Corrige les mots de passe de démonstration"""
    db = SessionLocal()
    try:
        # Corriger le mot de passe admin@demo.com
        admin_demo = db.query(models.HRAdmin).filter(models.HRAdmin.email == "admin@demo.com").first()
        if admin_demo:
            # Le mot de passe demo est "admin123"
            new_hash = hash_password("admin123")
            admin_demo.password_hash = new_hash
            print("✅ Mot de passe admin@demo.com corrigé")
        
        # Corriger le mot de passe hr@techcorp.com  
        hr_demo = db.query(models.HRAdmin).filter(models.HRAdmin.email == "hr@techcorp.com").first()
        if hr_demo:
            # Le mot de passe demo est "admin123"
            new_hash = hash_password("admin123")
            hr_demo.password_hash = new_hash
            print("✅ Mot de passe hr@techcorp.com corrigé")
        
        db.commit()
        print("✅ Tous les mots de passe ont été corrigés!")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erreur: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    fix_demo_passwords()
