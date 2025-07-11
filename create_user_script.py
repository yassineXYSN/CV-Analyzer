#!/usr/bin/env python3
"""
Script pour créer des utilisateurs via ligne de commande
"""

from auth_utils import create_admin_user, test_login
from company_utils import get_user_company, add_user_to_company
import sys

def create_user_interactive():
    """Créer un utilisateur de manière interactive"""
    print("👤 Création d'un nouvel utilisateur")
    print("=" * 40)
    
    # Demander les informations
    email = input("Email: ").strip()
    if not email:
        print("❌ Email requis")
        return
    
    password = input("Mot de passe: ").strip()
    if not password:
        print("❌ Mot de passe requis")
        return
    
    first_name = input("Prénom: ").strip()
    if not first_name:
        print("❌ Prénom requis")
        return
    
    last_name = input("Nom: ").strip()
    if not last_name:
        print("❌ Nom requis")
        return
    
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
    
    # Créer l'utilisateur
    print(f"\n📝 Création de l'utilisateur...")
    user_id = create_admin_user(email, password, first_name, last_name, role)
    
    if not user_id:
        print("❌ Échec de la création")
        return
    
    print(f"✅ Utilisateur créé avec ID: {user_id}")
    
    # Tester la connexion
    print("🧪 Test de connexion...")
    if test_login(email, password):
        print("✅ Test de connexion réussi")
    else:
        print("❌ Test de connexion échoué")
    
    # Demander s'il faut ajouter à une entreprise
    add_to_company = input("\nAjouter à une entreprise existante ? (y/N): ").strip().lower()
    if add_to_company == 'y':
        company_id = input("ID de l'entreprise: ").strip()
        if company_id.isdigit():
            access_level = input("Niveau d'accès (admin/viewer/owner, défaut=admin): ").strip() or "admin"
            
            success, message = add_user_to_company(
                company_id=int(company_id),
                admin_id=user_id,
                access_level=access_level
            )
            
            if success:
                print(f"✅ {message}")
            else:
                print(f"❌ {message}")
    
    print(f"\n✅ Utilisateur {email} créé avec succès !")

def create_user_batch():
    """Créer plusieurs utilisateurs en lot"""
    print("👥 Création d'utilisateurs en lot")
    print("=" * 40)
    
    users = [
        {
            "email": "manager@demo.com",
            "password": "manager123",
            "first_name": "Marie",
            "last_name": "Manager",
            "role": "hr_manager"
        },
        {
            "email": "viewer@demo.com",
            "password": "viewer123",
            "first_name": "Jean",
            "last_name": "Viewer",
            "role": "hr_admin"
        }
    ]
    
    for user_data in users:
        print(f"\n➕ Création de {user_data['email']}...")
        
        user_id = create_admin_user(
            email=user_data["email"],
            password=user_data["password"],
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
            role=user_data["role"]
        )
        
        if user_id:
            print(f"✅ Utilisateur créé avec ID: {user_id}")
            
            # Tester la connexion
            if test_login(user_data["email"], user_data["password"]):
                print(f"✅ Test de connexion réussi")
            else:
                print(f"❌ Test de connexion échoué")
        else:
            print(f"❌ Échec de création")
    
    print(f"\n✅ Création en lot terminée")

def main():
    """Menu principal"""
    if len(sys.argv) > 1 and sys.argv[1] == "batch":
        create_user_batch()
    else:
        create_user_interactive()

if __name__ == "__main__":
    main()
