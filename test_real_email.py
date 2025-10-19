#!/usr/bin/env python3
"""
Test Real Email Sending
This script tests sending a real email using the interview notification service.
"""

import os
import sys

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils1.interview_notifications import InterviewNotificationService

def test_real_email():
    """Test sending a real email"""
    print("=" * 60)
    print("CV Analyzer Pro - Real Email Test")
    print("=" * 60)
    
    # Use your email address for testing
    test_email = "cvanalyzerpro25@gmail.com"  # Using the same email as SMTP username
    print(f"Using test email: {test_email}")
    
    print(f"\nSending test email to: {test_email}")
    print("-" * 40)
    
    try:
        # Initialize the service
        service = InterviewNotificationService()
        print("SUCCESS: Email service initialized")
        
        # Send test email
        subject = "Test Email - CV Analyzer Pro"
        html_content = """
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%); padding: 2rem; text-align: center; color: white;">
                <h1>CV Analyzer Pro</h1>
                <p>Test Email</p>
            </div>
            <div style="padding: 2rem;">
                <h2>Email Configuration Test</h2>
                <p>If you receive this email, your SMTP configuration is working correctly!</p>
                <p>This means the interview notification system is ready to use.</p>
                <div style="background: #f0f9ff; border: 1px solid #3b82f6; border-radius: 8px; padding: 1rem; margin: 1rem 0;">
                    <h3>Next Steps:</h3>
                    <ul>
                        <li>Test the interview notification system</li>
                        <li>Configure your application to use the email service</li>
                        <li>Set up interview scheduling workflows</li>
                    </ul>
                </div>
                <p>Best regards,<br>CV Analyzer Pro Team</p>
            </div>
        </body>
        </html>
        """
        
        text_content = """
        CV Analyzer Pro - Test Email
        
        If you receive this email, your SMTP configuration is working correctly!
        
        This means the interview notification system is ready to use.
        
        Next Steps:
        - Test the interview notification system
        - Configure your application to use the email service
        - Set up interview scheduling workflows
        
        Best regards,
        CV Analyzer Pro Team
        """
        
        print("Sending email...")
        result = service.send_email(test_email, subject, html_content, text_content)
        
        if result:
            print("SUCCESS: Test email sent successfully!")
            print("Check your inbox for the test email.")
        else:
            print("ERROR: Failed to send test email")
            
    except Exception as e:
        print(f"ERROR: Failed to send test email: {e}")
    
    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60)

if __name__ == "__main__":
    test_real_email()
