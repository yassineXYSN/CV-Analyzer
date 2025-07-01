#!/usr/bin/env python3
"""
Script pour corriger le problème de redirection
"""

from database import SessionLocal
import models

def fix_company_setup_status():
    """S'assurer que toutes les entreprises ont setup_completed = True"""
    print("🔧 Correction du statut setup_completed")
    print("=" * 40)
    
    db = SessionLocal()
    try:
        # Récupérer toutes les entreprises
        companies = db.query(models.Company).all()
        
        for company in companies:
            print(f"\n🏢 Entreprise: {company.company_name}")
            print(f"   ID: {company.id}")
            print(f"   Setup completed avant: {company.setup_completed}")
            
            # Forcer setup_completed à True si l'entreprise a un nom
            if company.company_name and not company.setup_completed:
                company.setup_completed = True
                print(f"   ✅ Setup completed mis à jour: True")
            else:
                print(f"   ✅ Setup completed déjà correct")
        
        db.commit()
        print(f"\n✅ Correction terminée")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

def test_after_fix():
    """Tester après la correction"""
    print("\n🧪 Test après correction")
    print("=" * 40)
    
    from company_utils import check_user_company_status
    
    # Tester pour l'utilisateur admin@demo.com
    db = SessionLocal()
    try:
        user = db.query(models.HRAdmin).filter(models.HRAdmin.email == "admin@demo.com").first()
        
        if user:
            status = check_user_company_status(user.id)
            print(f"👤 Utilisateur: {user.email}")
            print(f"📊 Statut: {status}")
            
            if status['setup_completed']:
                print("✅ L'utilisateur devrait être redirigé vers /dashboard")
            else:
                print("⚠️  L'utilisateur sera redirigé vers /company-setup")
        else:
            print("❌ Utilisateur non trouvé")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    fix_company_setup_status()
    test_after_fix()
