#!/usr/bin/env python3
"""
Script pour configurer les utilisateurs de démonstration
"""

from auth_utils import create_admin_user, test_login
from database import SessionLocal
import models

def setup_demo_data():
    """Configure les données de démonstration"""
    
    print("🔧 Configuration des utilisateurs de démonstration")
    print("=" * 50)
    
    # Créer les utilisateurs de démonstration
    demo_users = [
        {
            "email": "admin@demo.com",
            "password": "admin123",
            "first_name": "Admin",
            "last_name": "Demo",
            "role": "super_admin"
        },
        {
            "email": "hr@techcorp.com",
            "password": "admin123", 
            "first_name": "Sarah",
            "last_name": "Johnson",
            "role": "hr_admin"
        },
        {
            "email": "manager@techcorp.com",
            "password": "manager123",
            "first_name": "John",
            "last_name": "Smith", 
            "role": "hr_manager"
        }
    ]
    
    db = SessionLocal()
    try:
        for user_data in demo_users:
            # Vérifier si l'utilisateur existe déjà
            existing_user = db.query(models.HRAdmin).filter(
                models.HRAdmin.email == user_data["email"]
            ).first()
            
            if existing_user:
                print(f"⚠️  L'utilisateur {user_data['email']} existe déjà")
                continue
            
            # Créer l'utilisateur
            admin_id = create_admin_user(
                email=user_data["email"],
                password=user_data["password"],
                first_name=user_data["first_name"],
                last_name=user_data["last_name"],
                role=user_data["role"]
            )
            
            if admin_id:
                print(f"✅ Utilisateur {user_data['email']} créé avec succès")
                
                # Tester la connexion
                if test_login(user_data["email"], user_data["password"]):
                    print(f"✅ Test de connexion réussi pour {user_data['email']}")
                else:
                    print(f"❌ Test de connexion échoué pour {user_data['email']}")
            else:
                print(f"❌ Échec de création pour {user_data['email']}")
                
    except Exception as e:
        print(f"❌ Erreur: {e}")
    finally:
        db.close()
    
    print(f"\n{'=' * 50}")
    print("✅ Configuration terminée")
    print("\n📋 Comptes de démonstration disponibles:")
    print("   • admin@demo.com / admin123 (Super Admin)")
    print("   • hr@techcorp.com / admin123 (HR Admin)")
    print("   • manager@techcorp.com / manager123 (HR Manager)")

if __name__ == "__main__":
    setup_demo_data()
