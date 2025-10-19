#!/usr/bin/env python3
"""
Debug Email Service
This script tests the email service with detailed error reporting.
"""

import os
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils1.interview_notifications import InterviewNotificationService

def test_email_service():
    """Test the email service with detailed debugging"""
    print("=" * 60)
    print("CV Analyzer Pro - Email Service Debug")
    print("=" * 60)
    
    # Check environment variables
    print("\n1. Checking Environment Variables:")
    print("-" * 40)
    
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = os.getenv("SMTP_PORT", "587")
    smtp_username = os.getenv("SMTP_USERNAME", "your-email@gmail.com")
    smtp_password = os.getenv("SMTP_PASSWORD", "your-app-password")
    from_email = os.getenv("FROM_EMAIL", "noreply@cvanalyzer.com")
    
    print(f"SMTP_SERVER: {smtp_server}")
    print(f"SMTP_PORT: {smtp_port}")
    print(f"SMTP_USERNAME: {smtp_username}")
    print(f"SMTP_PASSWORD: {'*' * len(smtp_password) if smtp_password else 'NOT SET'}")
    print(f"FROM_EMAIL: {from_email}")
    
    # Check if using default values
    if smtp_username == "your-email@gmail.com" or smtp_password == "your-app-password":
        print("\n❌ WARNING: Using default values! Please set your SMTP credentials.")
        print("\nTo set environment variables in Windows PowerShell:")
        print("$env:SMTP_USERNAME = 'your-actual-email@gmail.com'")
        print("$env:SMTP_PASSWORD = 'your-app-password'")
        print("$env:SMTP_SERVER = 'smtp.gmail.com'")
        print("$env:SMTP_PORT = '587'")
        print("$env:FROM_EMAIL = 'noreply@cvanalyzer.com'")
        return False
    
    print("\n2. Testing Email Service:")
    print("-" * 40)
    
    try:
        # Initialize the service
        service = InterviewNotificationService()
        print("SUCCESS: Email service initialized successfully")
        
        # Test email sending
        test_to = "test@example.com"  # This will fail, but we'll see the error
        test_subject = "Test Email"
        test_html = "<h1>Test</h1>"
        test_text = "Test"
        
        print(f"Attempting to send test email to {test_to}...")
        result = service.send_email(test_to, test_subject, test_html, test_text)
        
        if result:
            print("SUCCESS: Email sent successfully!")
        else:
            print("ERROR: Email sending failed")
            
    except Exception as e:
        print(f"ERROR: Error testing email service: {e}")
        print(f"Error type: {type(e).__name__}")
        
        # Provide specific help based on error type
        if "Authentication failed" in str(e):
            print("\nAUTHENTICATION ERROR:")
            print("- Check your email and password")
            print("- For Gmail: Use App Password, not regular password")
            print("- Enable 2-factor authentication first")
        elif "Connection refused" in str(e):
            print("\nCONNECTION ERROR:")
            print("- Check SMTP server and port")
            print("- Check your internet connection")
        elif "TLS" in str(e):
            print("\nTLS ERROR:")
            print("- Try different port (465 for SSL, 587 for TLS)")
        else:
            print(f"\nUNKNOWN ERROR: {e}")
    
    print("\n3. Manual SMTP Test:")
    print("-" * 40)
    
    try:
        print("Testing direct SMTP connection...")
        with smtplib.SMTP(smtp_server, int(smtp_port)) as server:
            print("SUCCESS: Connected to SMTP server")
            server.starttls()
            print("SUCCESS: TLS started")
            server.login(smtp_username, smtp_password)
            print("SUCCESS: Login successful")
            print("SUCCESS: SMTP configuration is working!")
    except Exception as e:
        print(f"ERROR: Direct SMTP test failed: {e}")
    
    print("\n" + "=" * 60)
    print("Debug complete!")
    print("=" * 60)

if __name__ == "__main__":
    test_email_service()
