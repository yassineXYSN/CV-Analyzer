import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from datetime import datetime, timedelta
import secrets
from sqlalchemy.orm import Session
from databasehr.database import get_db
from databasehr.models import HRAdmin

class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", 587))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
    
    def send_verification_email(self, email: str, token: str, user_name: str = "Utilisateur"):
        """Envoyer un email de vérification"""
        try:
            # Configuration du message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.smtp_username
            msg['To'] = email
            msg['Subject'] = "Vérifiez votre compte - CV Analyzer Pro"
            
            # Corps du message HTML stylisé
            verification_url = f"http://localhost:8000/admin/verify-email?token={token}"
            html_body = f"""
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
                        <p style="color: #e0e7ff; margin: 0.5rem 0 0 0;">Vérification de votre compte administrateur</p>
                    </div>
                    
                    <!-- Content -->
                    <div style="padding: 2rem;">
                        <h2 style="color: #1e293b; margin-bottom: 1rem;">Bonjour {user_name} !</h2>
                        
                        <p style="color: #64748b; line-height: 1.6; margin-bottom: 1.5rem;">
                            Merci de vous être inscrit en tant qu'administrateur sur CV Analyzer Pro ! Pour activer votre compte et accéder au tableau de bord d'administration, 
                            veuillez cliquer sur le bouton ci-dessous pour vérifier votre adresse email.
                        </p>
                        
                        <!-- Verification Button -->
                        <div style="text-align: center; margin: 2rem 0;">
                            <a href="{verification_url}" 
                               style="display: inline-block; background: linear-gradient(135deg, #10b981 0%, #059669 100%); 
                                      color: white; text-decoration: none; padding: 1rem 2rem; border-radius: 8px; 
                                      font-weight: 600; font-size: 1rem; transition: all 0.3s ease;">
                                ✅ Vérifier mon compte administrateur
                            </a>
                        </div>
                        
                        <p style="color: #64748b; font-size: 0.9rem; margin-bottom: 1.5rem;">
                            Si le bouton ne fonctionne pas, copiez et collez ce lien dans votre navigateur :
                        </p>
                        
                        <div style="background: #f1f5f9; padding: 1rem; border-radius: 8px; word-break: break-all; font-family: monospace; font-size: 0.9rem; color: #475569;">
                            {verification_url}
                        </div>
                        
                        <!-- Features -->
                        <div style="margin: 2rem 0; padding: 1.5rem; background: #f8fafc; border-radius: 8px;">
                            <h3 style="color: #1e293b; margin-bottom: 1rem;">Accès administrateur :</h3>
                            <ul style="color: #64748b; line-height: 1.6; margin: 0; padding-left: 1.5rem;">
                                <li>Gestion des utilisateurs et des entreprises</li>
                                <li>Tableau de bord analytique complet</li>
                                <li>Configuration des paramètres système</li>
                                <li>Suivi des activités et des performances</li>
                            </ul>
                        </div>
                        
                        <!-- Security Notice -->
                        <div style="border-left: 4px solid #fbbf24; padding: 1rem; background: #fef3c7; border-radius: 0 8px 8px 0; margin: 1.5rem 0;">
                            <p style="color: #92400e; margin: 0; font-size: 0.9rem;">
                                <strong>🔒 Sécurité :</strong> Ce lien de vérification expire dans 24 heures. 
                                Si vous n'avez pas créé de compte administrateur sur CV Analyzer Pro, ignorez cet email.
                            </p>
                        </div>
                    </div>
                    
                    <!-- Footer -->
                    <div style="background: #f1f5f9; padding: 1.5rem; text-align: center; border-top: 1px solid #e2e8f0;">
                        <p style="color: #64748b; margin: 0; font-size: 0.9rem;">
                            © 2024 CV Analyzer Pro. Tous droits réservés.
                        </p>
                        <p style="color: #94a3b8; margin: 0.5rem 0 0 0; font-size: 0.8rem;">
                            Cet email a été envoyé à votre demande lors de votre inscription administrateur.
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Version texte simple
            text_body = f"""
            Bonjour {user_name} !
            
            Merci de vous être inscrit en tant qu'administrateur sur CV Analyzer Pro !
            
            Pour activer votre compte administrateur, cliquez sur ce lien :
            {verification_url}
            
            Ce lien expire dans 24 heures.
            
            Si vous n'avez pas créé de compte administrateur, ignorez cet email.
            
            Cordialement,
            L'équipe CV Analyzer Pro
            """
            
            # Attacher les deux versions
            text_part = MIMEText(text_body, 'plain')
            html_part = MIMEText(html_body, 'html')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Envoi de l'email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            print(f"✅ Email de vérification envoyé à {email}")
            return True
        except Exception as e:
            print(f"❌ Erreur lors de l'envoi de l'email à {email}: {e}")
            return False

def generate_verification_token():
    """Générer un token de vérification sécurisé"""
    return secrets.token_urlsafe(32)

def save_verification_token(db: Session, user_id: int, token: str):
    """Sauvegarder le token de vérification dans la base de données"""
    user = db.query(HRAdmin).filter(HRAdmin.id == user_id).first()
    if user:
        user.verification_token = token
        user.token_expires = datetime.now() + timedelta(hours=24)
        db.commit()
        return True
    return False

def verify_token(db: Session, token: str):
    """Vérifier la validité d'un token et activer le compte"""
    user = db.query(HRAdmin).filter(HRAdmin.verification_token == token).first()
    if user and user.token_expires > datetime.now():
        user.is_verified = True
        user.is_active = True  # Activer le compte
        user.verification_token = None
        user.token_expires = None
        db.commit()
        return user
    return None