#!/usr/bin/env python3
"""
Simple Email Test - No Database Required
This script tests all email notification types with hardcoded data.
"""

import os
import sys
from datetime import datetime, timedelta

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils1.interview_notifications import InterviewNotificationService

def test_all_emails():
    """Test all email notification types with hardcoded data"""
    print("=" * 60)
    print("CV Analyzer Pro - Simple Email Test")
    print("=" * 60)
    
    # Initialize the email service
    service = InterviewNotificationService()
    print("SUCCESS: Email service initialized")
    
    # Test email address
    test_email = "yassinechtourou03@gmail.com"
    print(f"Testing emails to: {test_email}")
    print("-" * 60)
    
    # Test 1: HR notification when candidate chooses time
    print("TEST 1: HR notification when candidate chooses time")
    print("-" * 40)
    try:
        subject = "Candidat a choisi un créneau d'entretien - Test Candidate"
        html_content = """
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%); padding: 2rem; text-align: center; color: white;">
                <h1>CV Analyzer Pro</h1>
                <p>Notification HR</p>
            </div>
            <div style="padding: 2rem;">
                <h2>Candidat a choisi un créneau d'entretien</h2>
                <p><strong>Candidat:</strong> Test Candidate</p>
                <p><strong>Poste:</strong> Test Developer Position</p>
                <p><strong>Entreprise:</strong> Test Company</p>
                <p><strong>Date:</strong> 18/10/2025 à 22:30</p>
                <p>Le candidat a choisi ce créneau pour son entretien.</p>
            </div>
        </body>
        </html>
        """
        text_content = """
        CV Analyzer Pro - Notification HR
        
        Candidat a choisi un créneau d'entretien
        
        Candidat: Test Candidate
        Poste: Test Developer Position
        Entreprise: Test Company
        Date: 18/10/2025 à 22:30
        
        Le candidat a choisi ce créneau pour son entretien.
        """
        
        result = service.send_email(test_email, subject, html_content, text_content)
        if result:
            print("SUCCESS: HR choice notification sent!")
        else:
            print("ERROR: Failed to send HR choice notification")
    except Exception as e:
        print(f"ERROR: {e}")
    
    print()
    
    # Test 2: 24-hour reminder
    print("TEST 2: 24-hour reminder")
    print("-" * 40)
    try:
        subject = "Rappel entretien dans 24h - Test Developer Position"
        html_content = """
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); padding: 2rem; text-align: center; color: white;">
                <h1>CV Analyzer Pro</h1>
                <p>Rappel 24h</p>
            </div>
            <div style="padding: 2rem;">
                <h2>Rappel entretien dans 24h</h2>
                <p><strong>Poste:</strong> Test Developer Position</p>
                <p><strong>Entreprise:</strong> Test Company</p>
                <p><strong>Date:</strong> 18/10/2025 à 22:30</p>
                <p>Votre entretien aura lieu demain. Préparez-vous bien!</p>
            </div>
        </body>
        </html>
        """
        text_content = """
        CV Analyzer Pro - Rappel 24h
        
        Rappel entretien dans 24h
        
        Poste: Test Developer Position
        Entreprise: Test Company
        Date: 18/10/2025 à 22:30
        
        Votre entretien aura lieu demain. Préparez-vous bien!
        """
        
        result = service.send_email(test_email, subject, html_content, text_content)
        if result:
            print("SUCCESS: 24h reminder sent!")
        else:
            print("ERROR: Failed to send 24h reminder")
    except Exception as e:
        print(f"ERROR: {e}")
    
    print()
    
    # Test 3: 20-minute HR reminder
    print("TEST 3: 20-minute HR reminder")
    print("-" * 40)
    try:
        subject = "Entretien dans 20 minutes - Test Candidate"
        html_content = """
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); padding: 2rem; text-align: center; color: white;">
                <h1>CV Analyzer Pro</h1>
                <p>Rappel 20min</p>
            </div>
            <div style="padding: 2rem;">
                <h2>Entretien dans 20 minutes</h2>
                <p><strong>Candidat:</strong> Test Candidate</p>
                <p><strong>Poste:</strong> Test Developer Position</p>
                <p><strong>Entreprise:</strong> Test Company</p>
                <p>Préparez-vous pour l'entretien qui commence dans 20 minutes.</p>
            </div>
        </body>
        </html>
        """
        text_content = """
        CV Analyzer Pro - Rappel 20min
        
        Entretien dans 20 minutes
        
        Candidat: Test Candidate
        Poste: Test Developer Position
        Entreprise: Test Company
        
        Préparez-vous pour l'entretien qui commence dans 20 minutes.
        """
        
        result = service.send_email(test_email, subject, html_content, text_content)
        if result:
            print("SUCCESS: 20min HR reminder sent!")
        else:
            print("ERROR: Failed to send 20min HR reminder")
    except Exception as e:
        print(f"ERROR: {e}")
    
    print()
    
    # Test 4: 15-minute candidate reminder
    print("TEST 4: 15-minute candidate reminder")
    print("-" * 40)
    try:
        subject = "Entretien dans 15 minutes - Préparez-vous !"
        html_content = """
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%); padding: 2rem; text-align: center; color: white;">
                <h1>CV Analyzer Pro</h1>
                <p>Préparez-vous !</p>
            </div>
            <div style="padding: 2rem;">
                <h2>Entretien dans 15 minutes !</h2>
                <p><strong>Poste:</strong> Test Developer Position</p>
                <p><strong>Entreprise:</strong> Test Company</p>
                <h3>Checklist de préparation :</h3>
                <ul>
                    <li>Vérifiez votre connexion internet</li>
                    <li>Testez votre micro et caméra</li>
                    <li>Préparez vos questions</li>
                    <li>Installez-vous dans un endroit calme</li>
                </ul>
            </div>
        </body>
        </html>
        """
        text_content = """
        CV Analyzer Pro - Préparez-vous !
        
        Entretien dans 15 minutes !
        
        Poste: Test Developer Position
        Entreprise: Test Company
        
        Checklist de préparation :
        - Vérifiez votre connexion internet
        - Testez votre micro et caméra
        - Préparez vos questions
        - Installez-vous dans un endroit calme
        """
        
        result = service.send_email(test_email, subject, html_content, text_content)
        if result:
            print("SUCCESS: 15min candidate reminder sent!")
        else:
            print("ERROR: Failed to send 15min candidate reminder")
    except Exception as e:
        print(f"ERROR: {e}")
    
    print()
    
    # Test 5: 5-minute HR meeting link
    print("TEST 5: 5-minute HR meeting link")
    print("-" * 40)
    try:
        subject = "Lien de réunion - Entretien avec Test Candidate"
        html_content = """
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 2rem; text-align: center; color: white;">
                <h1>CV Analyzer Pro</h1>
                <p>Lien de réunion</p>
            </div>
            <div style="padding: 2rem;">
                <h2>Lien de réunion - Entretien avec Test Candidate</h2>
                <p><strong>Candidat:</strong> Test Candidate</p>
                <p><strong>Poste:</strong> Test Developer Position</p>
                <div style="background: #f0fdf4; border: 1px solid #10b981; border-radius: 8px; padding: 1rem; margin: 1rem 0;">
                    <h3>Lien de réunion:</h3>
                    <p><a href="https://zoom.com" style="color: #10b981; text-decoration: none; font-weight: bold;">https://zoom.com</a></p>
                </div>
                <p>L'entretien commence dans 5 minutes.</p>
            </div>
        </body>
        </html>
        """
        text_content = """
        CV Analyzer Pro - Lien de réunion
        
        Lien de réunion - Entretien avec Test Candidate
        
        Candidat: Test Candidate
        Poste: Test Developer Position
        
        Lien de réunion: https://zoom.com
        
        L'entretien commence dans 5 minutes.
        """
        
        result = service.send_email(test_email, subject, html_content, text_content)
        if result:
            print("SUCCESS: 5min HR meeting link sent!")
        else:
            print("ERROR: Failed to send 5min HR meeting link")
    except Exception as e:
        print(f"ERROR: {e}")
    
    print()
    
    # Test 6: Meeting time candidate link
    print("TEST 6: Meeting time candidate link")
    print("-" * 40)
    try:
        subject = "Votre entretien commence maintenant - Test Company"
        html_content = """
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%); padding: 2rem; text-align: center; color: white;">
                <h1>CV Analyzer Pro</h1>
                <p>C'est parti !</p>
            </div>
            <div style="padding: 2rem;">
                <h2>Votre entretien commence maintenant !</h2>
                <p><strong>Poste:</strong> Test Developer Position</p>
                <p><strong>Entreprise:</strong> Test Company</p>
                <div style="background: #faf5ff; border: 1px solid #8b5cf6; border-radius: 8px; padding: 1rem; margin: 1rem 0;">
                    <h3>Lien de réunion:</h3>
                    <p><a href="https://zoom.com" style="color: #8b5cf6; text-decoration: none; font-weight: bold;">https://zoom.com</a></p>
                </div>
                <p>Bonne chance pour votre entretien !</p>
            </div>
        </body>
        </html>
        """
        text_content = """
        CV Analyzer Pro - C'est parti !
        
        Votre entretien commence maintenant !
        
        Poste: Test Developer Position
        Entreprise: Test Company
        
        Lien de réunion: https://zoom.com
        
        Bonne chance pour votre entretien !
        """
        
        result = service.send_email(test_email, subject, html_content, text_content)
        if result:
            print("SUCCESS: Meeting time candidate link sent!")
        else:
            print("ERROR: Failed to send meeting time candidate link")
    except Exception as e:
        print(f"ERROR: {e}")
    
    print()
    print("=" * 60)
    print("All email tests completed!")
    print(f"Check your inbox at: {test_email}")
    print("=" * 60)

if __name__ == "__main__":
    test_all_emails()
