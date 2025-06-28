#!/usr/bin/env python3
"""
Script pour créer un nouvel administrateur HR
Usage: python create_admin.py
"""

from auth_utils import create_admin_user, test_login

def main():
    print("🔐 Création d'un nouvel administrateur HR")
    print("=" * 50)
    
    # Demander les informations
    email = input("Email: ").strip()
    password = input("Mot de passe: ").strip()
    first_name = input("Prénom: ").strip()
    last_name = input("Nom: ").strip()
    
    print("\nRôles disponibles:")
    print("1. hr_admin (par défaut)")
    print("2. hr_manager") 
    print("3. super_admin")
    
    role_choice = input("Choisir le rôle (1-3, défaut=1): ").strip()
    role_map = {
        "1": "hr_admin",
        "2": "hr_manager", 
        "3": "super_admin",
        "": "hr_admin"
    }
    role = role_map.get(role_choice, "hr_admin")
    
    print(f"\n📝 Création de l'utilisateur:")
    print(f"Email: {email}")
    print(f"Nom: {first_name} {last_name}")
    print(f"Rôle: {role}")
    
    confirm = input("\nConfirmer la création? (y/N): ").strip().lower()
    if confirm != 'y':
        print("❌ Création annulée")
        return
    
    # Créer l'utilisateur
    admin_id = create_admin_user(email, password, first_name, last_name, role)
    
    if admin_id:
        print(f"\n✅ Administrateur créé avec l'ID: {admin_id}")
        
        # Tester la connexion
        print("\n🧪 Test de connexion...")
        test_login(email, password)
    else:
        print("\n❌ Échec de la création")

if __name__ == "__main__":
    main()
