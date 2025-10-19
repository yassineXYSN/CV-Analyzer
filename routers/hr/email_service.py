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
        # Configuration temporaire - REMPLACEZ par vos vraies valeurs
        self.smtp_username = os.getenv("SMTP_USERNAME", "votre_email@gmail.com")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "votre_mot_de_passe")
    
    def send_verification_email(self, email: str, token: str, user_name: str = "Utilisateur"):
        """Envoyer un email de vérification"""
        try:
            # Configuration du message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.smtp_username
            msg['To'] = email
            msg['Subject'] = "Vérifiez votre compte - CV Analyzer Pro"
            
            # Corps du message HTML stylisé
            verification_url = f"http://localhost:8000/super-admin/verify-email?token={token}"
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
    
    def send_interview_invitation_email(self, candidate_email: str, candidate_name: str, job_title: str, company_name: str, interview_slots: list):
        """Envoyer un email d'invitation pour choisir un créneau d'entretien"""
        try:
            # Vérifier la configuration SMTP
            if not self.smtp_username or not self.smtp_password or self.smtp_username == "votre_email@gmail.com":
                print("⚠️ Mode test: Configuration SMTP non configurée")
                print(f"📧 Email simulé envoyé à: {candidate_email}")
                print(f"📝 Sujet: Invitation à un entretien - {job_title} chez {company_name}")
                print(f"👤 Candidat: {candidate_name}")
                print(f"📅 Créneaux: {len(interview_slots)} créneau(x)")
                return True
            # Configuration du message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.smtp_username
            msg['To'] = candidate_email
            msg['Subject'] = f"Invitation à un entretien - {job_title} chez {company_name}"
            
            # Formater les créneaux disponibles
            slots_html = ""
            for i, slot in enumerate(interview_slots, 1):
                start_time = slot['start_time'].strftime('%d/%m/%Y à %H:%M')
                end_time = slot['end_time'].strftime('%H:%M')
                slots_html += f"""
                <div style="background: #f8fafc; padding: 1rem; border-radius: 8px; margin: 0.5rem 0; border-left: 4px solid #3b82f6;">
                    <strong>Créneau {i} :</strong> {start_time} - {end_time}
                </div>
                """
            
            # Corps du message HTML stylisé
            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Invitation à un entretien - {job_title}</title>
            </head>
            <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8fafc;">
                <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                    <!-- Header -->
                    <div style="background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%); padding: 2rem; text-align: center;">
                        <h1 style="color: white; margin: 0; font-size: 1.5rem;">
                            🎯 Invitation à un entretien
                        </h1>
                        <p style="color: #e0e7ff; margin: 0.5rem 0 0 0;">{company_name}</p>
                    </div>
                    
                    <!-- Content -->
                    <div style="padding: 2rem;">
                        <h2 style="color: #1e293b; margin-bottom: 1rem;">Bonjour {candidate_name} !</h2>
                        
                        <p style="color: #64748b; line-height: 1.6; margin-bottom: 1.5rem;">
                            Nous avons le plaisir de vous informer que votre candidature pour le poste de <strong>{job_title}</strong> 
                            chez <strong>{company_name}</strong> a retenu notre attention !
                        </p>
                        
                        <p style="color: #64748b; line-height: 1.6; margin-bottom: 1.5rem;">
                            Nous aimerions vous rencontrer pour un entretien. Voici les créneaux disponibles :
                        </p>
                        
                        <!-- Créneaux disponibles -->
                        <div style="margin: 2rem 0;">
                            <h3 style="color: #1e293b; margin-bottom: 1rem;">📅 Créneaux disponibles :</h3>
                            {slots_html}
                        </div>
                        
                        <!-- Call to Action -->
                        <div style="text-align: center; margin: 2rem 0; padding: 1.5rem; background: #f0f9ff; border-radius: 8px; border: 1px solid #bfe2ff;">
                            <p style="color: #1e40af; margin: 0 0 1rem 0; font-weight: 600;">
                                🚀 Choisissez votre créneau préféré
                            </p>
                            <p style="color: #64748b; margin: 0; font-size: 0.9rem;">
                                Cliquez sur le bouton ci-dessous pour accéder à la page de sélection des créneaux
                            </p>
                            <div style="margin-top: 1rem;">
                                <a href="http://127.0.0.1:8000/notifications" 
                                   style="display: inline-block; background: linear-gradient(135deg, #10b981 0%, #059669 100%); 
                                          color: white; text-decoration: none; padding: 1rem 2rem; border-radius: 8px; 
                                          font-weight: 600; font-size: 1rem; transition: all 0.3s ease;">
                                    📝 Choisir mon créneau
                                </a>
                            </div>
                        </div>
                        
                        <!-- Instructions -->
                        <div style="margin: 2rem 0; padding: 1.5rem; background: #f8fafc; border-radius: 8px;">
                            <h3 style="color: #1e293b; margin-bottom: 1rem;">📋 Instructions :</h3>
                            <ul style="color: #64748b; line-height: 1.6; margin: 0; padding-left: 1.5rem;">
                                <li>Sélectionnez le créneau qui vous convient le mieux</li>
                                <li>Vous recevrez une confirmation par email</li>
                                <li>En cas d'empêchement, contactez-nous rapidement</li>
                                <li>Préparez-vous à nous parler de votre expérience</li>
                            </ul>
                        </div>
                        
                        <!-- Contact Info -->
                        <div style="border-left: 4px solid #3b82f6; padding: 1rem; background: #f0f9ff; border-radius: 0 8px 8px 0; margin: 1.5rem 0;">
                            <p style="color: #1e40af; margin: 0; font-size: 0.9rem;">
                                <strong>📞 Besoin d'aide ?</strong> Si vous avez des questions ou des difficultés, 
                                n'hésitez pas à nous contacter. Nous sommes là pour vous accompagner !
                            </p>
                        </div>
                    </div>
                    
                    <!-- Footer -->
                    <div style="background: #f1f5f9; padding: 1.5rem; text-align: center; border-top: 1px solid #e2e8f0;">
                        <p style="color: #64748b; margin: 0; font-size: 0.9rem;">
                            © 2024 {company_name}. Tous droits réservés.
                        </p>
                        <p style="color: #94a3b8; margin: 0.5rem 0 0 0; font-size: 0.8rem;">
                            Cet email a été envoyé dans le cadre de votre candidature.
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Version texte simple
            text_body = f"""
            Bonjour {candidate_name} !
            
            Nous avons le plaisir de vous informer que votre candidature pour le poste de {job_title} 
            chez {company_name} a retenu notre attention !
            
            Nous aimerions vous rencontrer pour un entretien. Voici les créneaux disponibles :
            
            """
            
            for i, slot in enumerate(interview_slots, 1):
                start_time = slot['start_time'].strftime('%d/%m/%Y à %H:%M')
                end_time = slot['end_time'].strftime('%H:%M')
                text_body += f"Creneau {i}: {start_time} - {end_time}\n"
            
            text_body += f"""
            
            Pour choisir votre créneau, cliquez sur le lien suivant :
            http://127.0.0.1:8000/notifications
            
            Instructions :
            - Sélectionnez le créneau qui vous convient le mieux
            - Vous recevrez une confirmation par email
            - En cas d'empêchement, contactez-nous rapidement
            
            Cordialement,
            L'équipe {company_name}
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
            
            print(f"✅ Email d'invitation envoyé à {candidate_email}")
            return True
        except Exception as e:
            print(f"❌ Erreur lors de l'envoi de l'email d'invitation à {candidate_email}: {e}")
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