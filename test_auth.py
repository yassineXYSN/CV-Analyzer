#!/usr/bin/env python3
"""
Script de test pour l'authentification HR
"""

import asyncio
import aiohttp
import json

async def test_login_api():
    """Test de l'API de connexion"""
    
    test_cases = [
        {
            "name": "Connexion valide - admin@demo.com",
            "email": "admin@demo.com",
            "password": "admin123",
            "should_succeed": True
        },
        {
            "name": "Connexion valide - hr@techcorp.com", 
            "email": "hr@techcorp.com",
            "password": "admin123",
            "should_succeed": True
        },
        {
            "name": "Email inexistant",
            "email": "inexistant@test.com",
            "password": "password123",
            "should_succeed": False
        },
        {
            "name": "Mot de passe incorrect",
            "email": "admin@demo.com", 
            "password": "mauvais_password",
            "should_succeed": False
        },
        {
            "name": "Email vide",
            "email": "",
            "password": "admin123",
            "should_succeed": False
        }
    ]
    
    base_url = "http://localhost:8000"
    
    async with aiohttp.ClientSession() as session:
        print("🧪 Test de l'API d'authentification HR")
        print("=" * 50)
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{i}. {test_case['name']}")
            print(f"   Email: {test_case['email']}")
            print(f"   Password: {'*' * len(test_case['password'])}")
            
            try:
                async with session.post(
                    f"{base_url}/api/hr-login",
                    json={
                        "email": test_case['email'],
                        "password": test_case['password']
                    },
                    headers={"Content-Type": "application/json"}
                ) as response:
                    
                    result = await response.json()
                    
                    if test_case['should_succeed']:
                        if result.get('success'):
                            print(f"   ✅ SUCCÈS: {result.get('message')}")
                            print(f"   🔗 Redirection: {result.get('redirect_url')}")
                        else:
                            print(f"   ❌ ÉCHEC INATTENDU: {result.get('message')}")
                    else:
                        if not result.get('success'):
                            print(f"   ✅ ÉCHEC ATTENDU: {result.get('message')}")
                        else:
                            print(f"   ❌ SUCCÈS INATTENDU: {result.get('message')}")
                            
            except Exception as e:
                print(f"   ❌ ERREUR: {str(e)}")
        
        print(f"\n{'=' * 50}")
        print("✅ Tests terminés")

if __name__ == "__main__":
    print("Assurez-vous que votre serveur FastAPI est démarré sur localhost:8000")
    input("Appuyez sur Entrée pour continuer...")
    asyncio.run(test_login_api())
