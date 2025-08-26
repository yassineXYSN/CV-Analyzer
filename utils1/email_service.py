import smtplib
import secrets
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Optional
import os

# Email configuration - set these in your environment variables
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "your-email@gmail.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "your-app-password")
FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@cvanalyzer.com")
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

def generate_verification_token() -> str:
    """Generate a secure verification token"""
    return secrets.token_urlsafe(32)

def create_verification_email_html(user_name: str, verification_link: str) -> str:
    """Create HTML email template for verification"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Vérifiez votre compte - CV Analyzer Pro</title>
    </head>
    <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8fafc;">
        <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
            <!-- Header -->
            <div style="background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%); padding: 2rem; text-align: center;">
                <h1 style="color: white; margin: 0; font-size: 1.5rem;">
                    🧠 CV Analyzer Pro
                </h1>
                <p style="color: #e0e7ff; margin: 0.5rem 0 0 0;">Vérification de votre compte</p>
            </div>
            
            <!-- Content -->
            <div style="padding: 2rem;">
                <h2 style="color: #1e293b; margin-bottom: 1rem;">Bonjour {user_name} !</h2>
                
                <p style="color: #64748b; line-height: 1.6; margin-bottom: 1.5rem;">
                    Merci de vous être inscrit sur CV Analyzer Pro ! Pour activer votre compte et commencer à analyser vos CV, 
                    veuillez cliquer sur le bouton ci-dessous pour vérifier votre adresse email.
                </p>
                
                <!-- Verification Button -->
                <div style="text-align: center; margin: 2rem 0;">
                    <a href="{verification_link}" 
                       style="display: inline-block; background: linear-gradient(135deg, #10b981 0%, #059669 100%); 
                              color: white; text-decoration: none; padding: 1rem 2rem; border-radius: 8px; 
                              font-weight: 600; font-size: 1rem; transition: all 0.3s ease;">
                        ✅ Vérifier mon compte
                    </a>
                </div>
                
                <p style="color: #64748b; font-size: 0.9rem; margin-bottom: 1.5rem;">
                    Si le bouton ne fonctionne pas, copiez et collez ce lien dans votre navigateur :
                </p>
                
                <div style="background: #f1f5f9; padding: 1rem; border-radius: 8px; word-break: break-all; font-family: monospace; font-size: 0.9rem; color: #475569;">
                    {verification_link}
                </div>
                
                <!-- Features -->
                <div style="margin: 2rem 0; padding: 1.5rem; background: #f8fafc; border-radius: 8px;">
                    <h3 style="color: #1e293b; margin-bottom: 1rem;">Ce qui vous attend :</h3>
                    <ul style="color: #64748b; line-height: 1.6; margin: 0; padding-left: 1.5rem;">
                        <li>Analyse intelligente de vos CV par IA</li>
                        <li>Recommandations personnalisées d'amélioration</li>
                        <li>Score de compatibilité avec les offres d'emploi</li>
                        <li>Suivi de vos candidatures</li>
                    </ul>
                </div>
                
                <!-- Security Notice -->
                <div style="border-left: 4px solid #fbbf24; padding: 1rem; background: #fef3c7; border-radius: 0 8px 8px 0; margin: 1.5rem 0;">
                    <p style="color: #92400e; margin: 0; font-size: 0.9rem;">
                        <strong>🔒 Sécurité :</strong> Ce lien de vérification expire dans 24 heures. 
                        Si vous n'avez pas créé de compte sur CV Analyzer Pro, ignorez cet email.
                    </p>
                </div>
            </div>
            
            <!-- Footer -->
            <div style="background: #f1f5f9; padding: 1.5rem; text-align: center; border-top: 1px solid #e2e8f0;">
                <p style="color: #64748b; margin: 0; font-size: 0.9rem;">
                    © 2024 CV Analyzer Pro. Tous droits réservés.
                </p>
                <p style="color: #94a3b8; margin: 0.5rem 0 0 0; font-size: 0.8rem;">
                    Cet email a été envoyé à votre demande lors de votre inscription.
                </p>
            </div>
        </div>
    </body>
    </html>
    """

def send_verification_email(to_email: str, user_name: str, verification_token: str) -> bool:
    """Send verification email to user"""
    try:
        # Create verification link
        verification_link = f"{BASE_URL}/auth/verify-email?token={verification_token}"
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "Vérifiez votre compte - CV Analyzer Pro"
        msg['From'] = FROM_EMAIL
        msg['To'] = to_email
        
        # Create HTML content
        html_content = create_verification_email_html(user_name, verification_link)
        html_part = MIMEText(html_content, 'html')
        
        # Create plain text version
        text_content = f"""
        Bonjour {user_name} !
        
        Merci de vous être inscrit sur CV Analyzer Pro !
        
        Pour activer votre compte, cliquez sur ce lien :
        {verification_link}
        
        Ce lien expire dans 24 heures.
        
        Si vous n'avez pas créé de compte, ignorez cet email.
        
        Cordialement,
        L'équipe CV Analyzer Pro
        """
        text_part = MIMEText(text_content, 'plain')
        
        # Attach parts
        msg.attach(text_part)
        msg.attach(html_part)
        
        # Send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        
        print(f"✅ Verification email sent to {to_email}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send verification email to {to_email}: {e}")
        return False

def get_verification_token_expiry() -> datetime:
    """Get expiry time for verification token (24 hours from now)"""
    return datetime.utcnow() + timedelta(hours=24)
