"""
Script de test complet du flux de connexion et configuration
"""

import requests
import json

def test_complete_flow():
    """Test le flux complet : login → vérification entreprise → redirection"""
    
    base_url = "http://localhost:8000"
    
    print("🧪 DÉBUT TEST COMPLET DU FLUX")
    print("=" * 50)
    
    # Test 1: Login avec utilisateur sans entreprise
    print("\n🔐 TEST 1: Login utilisateur sans entreprise")
    login_data = {
        "email": "admin@demo.com",
        "password": "admin123"
    }
    
    try:
        response = requests.post(f"{base_url}/api/hr-login", json=login_data)
        result = response.json()
        
        print(f"📥 Réponse login: {result}")
        
        if result.get('success'):
            print(f"✅ Login réussi")
            print(f"🎯 Redirection: {result.get('redirect_url')}")
            
            if result.get('redirect_url') == '/company-setup':
                print("✅ Redirection correcte vers company-setup")
            else:
                print("❌ Redirection incorrecte")
        else:
            print(f"❌ Login échoué: {result.get('message')}")
            
    except Exception as e:
        print(f"❌ Erreur login: {e}")
    
    # Test 2: Configuration entreprise
    print("\n🏢 TEST 2: Configuration entreprise")
    company_data = {
        "company_name": "Test Company",
        "industry": "tech",
        "company_size": "11-50",
        "founded_year": 2020,
        "description": "Une entreprise de test",
        "address": "123 Test Street",
        "phone": "+33123456789",
        "email": "contact@testcompany.com",
        "website": "https://testcompany.com"
    }
    
    try:
        response = requests.post(f"{base_url}/api/company-setup", json=company_data)
        result = response.json()
        
        print(f"📥 Réponse setup: {result}")
        
        if result.get('success'):
            print(f"✅ Configuration réussie")
            print(f"🎯 Redirection: {result.get('redirect_url')}")
            
            if result.get('redirect_url') == '/dashboard':
                print("✅ Redirection correcte vers dashboard")
            else:
                print("❌ Redirection incorrecte")
        else:
            print(f"❌ Configuration échouée: {result.get('message')}")
            
    except Exception as e:
        print(f"❌ Erreur configuration: {e}")
    
    # Test 3: Re-login après configuration
    print("\n🔐 TEST 3: Re-login après configuration")
    
    try:
        response = requests.post(f"{base_url}/api/hr-login", json=login_data)
        result = response.json()
        
        print(f"📥 Réponse re-login: {result}")
        
        if result.get('success'):
            print(f"✅ Re-login réussi")
            print(f"🎯 Redirection: {result.get('redirect_url')}")
            
            if result.get('redirect_url') == '/dashboard':
                print("✅ Redirection correcte vers dashboard (entreprise configurée)")
            else:
                print("❌ Redirection incorrecte - devrait aller au dashboard")
        else:
            print(f"❌ Re-login échoué: {result.get('message')}")
            
    except Exception as e:
        print(f"❌ Erreur re-login: {e}")
    
    print("\n" + "=" * 50)
    print("🧪 FIN TEST COMPLET DU FLUX")

if __name__ == "__main__":
    test_complete_flow()
