#!/usr/bin/env python3
"""
Script pour configurer les utilisateurs de démonstration
"""

from auth_utils import create_admin_user, test_login
from database import SessionLocal
import models

def setup_demo_users():
    """Configure les utilisateurs de démonstration"""
    print("👥 Configuration des utilisateurs de démonstration")
    print("=" * 50)
    
    # Supprimer les anciens utilisateurs
    db = SessionLocal()
    try:
        print("🗑️  Suppression des anciens utilisateurs...")
        db.query(models.HRAdmin).delete()
        db.commit()
        print("✅ Anciens utilisateurs supprimés")
    except Exception as e:
        print(f"⚠️  Erreur suppression: {e}")
        db.rollback()
    finally:
        db.close()
    
    # Créer les nouveaux utilisateurs
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
        }
    ]
    
    for user_data in demo_users:
        print(f"\n➕ Création de {user_data['email']}...")
        
        admin_id = create_admin_user(
            email=user_data["email"],
            password=user_data["password"],
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
            role=user_data["role"]
        )
        
        if admin_id:
            print(f"✅ Utilisateur créé avec ID: {admin_id}")
            
            # Tester immédiatement
            print(f"🧪 Test de connexion...")
            if test_login(user_data["email"], user_data["password"]):
                print(f"✅ Test réussi")
            else:
                print(f"❌ Test échoué")
        else:
            print(f"❌ Échec de création")
    
    print(f"\n{'=' * 50}")
    print("✅ Configuration terminée")
    print("\n📋 Comptes disponibles:")
    print("   • admin@demo.com / admin123")
    print("   • hr@techcorp.com / admin123")

if __name__ == "__main__":
    setup_demo_users()
