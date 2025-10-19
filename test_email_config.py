#!/usr/bin/env python3
"""
Email Configuration Test Script
This script helps you test and configure SMTP settings for the interview notification system.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

def test_smtp_connection(smtp_server, smtp_port, username, password, from_email, to_email):
    """Test SMTP connection and send a test email"""
    try:
        print(f"Testing SMTP connection...")
        print(f"Server: {smtp_server}:{smtp_port}")
        print(f"Username: {username}")
        print(f"From: {from_email}")
        print(f"To: {to_email}")
        print("-" * 50)
        
        # Create test email
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "Test Email - CV Analyzer Pro"
        msg['From'] = from_email
        msg['To'] = to_email
        
        text_content = """
        This is a test email from CV Analyzer Pro.
        
        If you receive this email, your SMTP configuration is working correctly!
        
        Best regards,
        CV Analyzer Pro Team
        """
        
        html_content = """
        <html>
        <body>
            <h2>Test Email - CV Analyzer Pro</h2>
            <p>This is a test email from CV Analyzer Pro.</p>
            <p><strong>If you receive this email, your SMTP configuration is working correctly!</strong></p>
            <p>Best regards,<br>CV Analyzer Pro Team</p>
        </body>
        </html>
        """
        
        text_part = MIMEText(text_content, 'plain')
        html_part = MIMEText(html_content, 'html')
        
        msg.attach(text_part)
        msg.attach(html_part)
        
        # Connect and send
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            print("Connecting to SMTP server...")
            server.starttls()
            print("Starting TLS...")
            server.login(username, password)
            print("Login successful!")
            server.send_message(msg)
            print("Email sent successfully!")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to send test email: {e}")
        return False

def main():
    print("=" * 60)
    print("CV Analyzer Pro - Email Configuration Test")
    print("=" * 60)
    
    # Get configuration from user
    print("\nPlease enter your SMTP configuration:")
    print("(Press Enter to use default values)")
    
    smtp_server = input("SMTP Server [smtp.gmail.com]: ").strip() or "smtp.gmail.com"
    smtp_port = input("SMTP Port [587]: ").strip() or "587"
    username = input("SMTP Username (your email): ").strip()
    password = input("SMTP Password (app password for Gmail): ").strip()
    from_email = input("From Email [noreply@cvanalyzer.com]: ").strip() or "noreply@cvanalyzer.com"
    to_email = input("Test Email (where to send test): ").strip()
    
    if not username or not password or not to_email:
        print("ERROR: Username, password, and test email are required!")
        return
    
    try:
        smtp_port = int(smtp_port)
    except ValueError:
        print("ERROR: Invalid port number!")
        return
    
    print("\n" + "=" * 60)
    print("Testing Email Configuration...")
    print("=" * 60)
    
    success = test_smtp_connection(smtp_server, smtp_port, username, password, from_email, to_email)
    
    print("\n" + "=" * 60)
    if success:
        print("SUCCESS: Email configuration is working!")
        print("\nTo use this configuration in your application:")
        print("Set these environment variables:")
        print(f"set SMTP_SERVER={smtp_server}")
        print(f"set SMTP_PORT={smtp_port}")
        print(f"set SMTP_USERNAME={username}")
        print(f"set SMTP_PASSWORD={password}")
        print(f"set FROM_EMAIL={from_email}")
    else:
        print("FAILED: Email configuration needs to be fixed.")
        print("\nCommon issues:")
        print("1. For Gmail: Use App Password instead of regular password")
        print("2. Enable 2-factor authentication first")
        print("3. Check if 'Less secure app access' is enabled")
        print("4. Verify SMTP server and port settings")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
