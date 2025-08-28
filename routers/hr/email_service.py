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
    
    def send_verification_email(self, email: str, token: str):
        """Envoyer un email de vérification"""
        try:
            # Configuration du message
            msg = MIMEMultipart()
            msg['From'] = self.smtp_username
            msg['To'] = email
            msg['Subject'] = "Vérification de votre compte"
            
            # Corps du message
            verification_url = f"http://localhost:8000/admin/verify-email?token={token}"
            body = f"""
            <html>
            <body>
                <h2>Vérification de votre compte</h2>
                <p>Bonjour,</p>
                <p>Merci de vous être inscrit. Veuillez cliquer sur le lien ci-dessous pour vérifier votre adresse email et activer votre compte :</p>
                <p><a href="{verification_url}">Vérifier mon email</a></p>
                <p>Ce lien expirera dans 24 heures.</p>
                <p>Après vérification, vous serez redirigé vers la page de connexion.</p>
                <p>Cordialement,<br>L'équipe d'administration</p>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(body, 'html'))
            
            # Envoi de l'email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            return True
        except Exception as e:
            print(f"Erreur lors de l'envoi de l'email: {e}")
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