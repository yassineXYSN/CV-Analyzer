import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import os
from typing import Optional
import asyncio
from sqlalchemy.orm import Session
from databasehr.database import SessionLocal
from databasehr.models import Application, Job, HRAdmin, Contact
from databaseclient.models import ProfileCandidat

# Email configuration
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "your-email@gmail.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "your-app-password")
FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@cvanalyzer.com")

class InterviewNotificationService:
    def __init__(self):
        self.smtp_server = SMTP_SERVER
        self.smtp_port = SMTP_PORT
        self.smtp_username = SMTP_USERNAME
        self.smtp_password = SMTP_PASSWORD
        self.from_email = FROM_EMAIL

    def send_email(self, to_email: str, subject: str, html_content: str, text_content: str) -> bool:
        """Send email with HTML and text content"""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email
            
            text_part = MIMEText(text_content, 'plain')
            html_part = MIMEText(html_content, 'html')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            print(f"SUCCESS: Email sent to {to_email}: {subject}")
            return True
        except Exception as e:
            print(f"ERROR: Failed to send email to {to_email}: {e}")
            return False

    def send_candidate_choice_notification_to_hr(self, application_id: int):
        """Send notification to HR when candidate chooses interview time"""
        try:
            db = SessionLocal()
            # Get application details
            application = db.query(Application).filter(Application.id == application_id).first()
            if not application:
                db.close()
                return False
            
            # Get candidate details
            candidate_name = application.candidate_profile.name if application.candidate_profile else "Candidat"
            candidate_email = application.candidate_profile.contact.email if application.candidate_profile and application.candidate_profile.contact else "email@example.com"
            
            # Get job details
            job = db.query(Job).filter(Job.id == application.job_id).first()
            job_title = job.title if job else "Poste"
            company_name = job.company.company_name if job and job.company else "Entreprise"
            
            # Get HR admin email
            hr_admin = db.query(HRAdmin).first()
            hr_email = hr_admin.email if hr_admin else "hr@company.com"
            
            # Format interview date/time
            interview_date = application.interview_date.strftime("%d/%m/%Y") if application.interview_date else "Date non définie"
            interview_time = application.interview_time if application.interview_time else "Heure non définie"
            
            subject = f" Candidat a choisi un créneau d'entretien - {candidate_name}"
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Choix de créneau d'entretien</title>
            </head>
            <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8fafc;">
                <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                    <!-- Header -->
                    <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 2rem; text-align: center;">
                        <h1 style="color: white; margin: 0; font-size: 1.5rem;">
 CV Analyzer Pro
                        </h1>
                        <p style="color: #d1fae5; margin: 0.5rem 0 0 0;">Notification d'entretien</p>
                    </div>
                    
                    <!-- Content -->
                    <div style="padding: 2rem;">
                        <h2 style="color: #1e293b; margin-bottom: 1rem;">Candidat a choisi un créneau !</h2>
                        
                        <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 1.5rem; margin: 1.5rem 0;">
                            <h3 style="color: #166534; margin: 0 0 1rem 0;"> Détails de l'entretien</h3>
                            <p style="color: #166534; margin: 0.5rem 0;"><strong>Candidat:</strong> {candidate_name}</p>
                            <p style="color: #166534; margin: 0.5rem 0;"><strong>Poste:</strong> {job_title}</p>
                            <p style="color: #166534; margin: 0.5rem 0;"><strong>Entreprise:</strong> {company_name}</p>
                            <p style="color: #166534; margin: 0.5rem 0;"><strong>Date:</strong> {interview_date}</p>
                            <p style="color: #166534; margin: 0.5rem 0;"><strong>Heure:</strong> {interview_time}</p>
                        </div>
                        
                        <p style="color: #64748b; line-height: 1.6;">
                            Le candidat <strong>{candidate_name}</strong> a confirmé son choix de créneau d'entretien. 
                            Vous pouvez maintenant préparer l'entretien et vous attendre à recevoir des rappels automatiques.
                        </p>
                        
                        <div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 1rem; border-radius: 0 8px 8px 0; margin: 1.5rem 0;">
                            <p style="color: #92400e; margin: 0; font-size: 0.9rem;">
                                <strong>📧 Rappels automatiques :</strong> Vous recevrez des rappels 24h avant, 20min avant, et le lien de réunion 5min avant l'entretien.
                            </p>
                        </div>
                    </div>
                    
                    <!-- Footer -->
                    <div style="background: #f1f5f9; padding: 1.5rem; text-align: center; border-top: 1px solid #e2e8f0;">
                        <p style="color: #64748b; margin: 0; font-size: 0.9rem;">
                            © 2024 CV Analyzer Pro. Tous droits réservés.
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            text_content = f"""
            Bonjour,
            
            Le candidat {candidate_name} a choisi un créneau d'entretien :
            
            - Candidat: {candidate_name}
            - Poste: {job_title}
            - Entreprise: {company_name}
            - Date: {interview_date}
            - Heure: {interview_time}
            
            Vous recevrez des rappels automatiques avant l'entretien.
            
            Cordialement,
            L'équipe CV Analyzer Pro
            """
            
            result = self.send_email(hr_email, subject, html_content, text_content)
            db.close()
            return result
            
        except Exception as e:
            print(f"ERROR: Error sending candidate choice notification: {e}")
            db.close()
            return False

    def send_24h_reminder(self, application_id: int):
        """Send 24-hour reminder to both HR and candidate"""
        try:
            db = SessionLocal()
            application = db.query(Application).filter(Application.id == application_id).first()
            if not application or not application.interview_date:
                db.close()
                return False
            
            # Get details
            candidate_name = application.candidate_profile.name if application.candidate_profile else "Candidat"
            candidate_email = application.candidate_profile.contact.email if application.candidate_profile and application.candidate_profile.contact else None
            
            job = db.query(Job).filter(Job.id == application.job_id).first()
            job_title = job.title if job else "Poste"
            company_name = job.company.company_name if job and job.company else "Entreprise"
            
            hr_admin = db.query(HRAdmin).first()
            hr_email = hr_admin.email if hr_admin else None
            
            interview_date = application.interview_date.strftime("%d/%m/%Y")
            interview_time = application.interview_time if application.interview_time else "Heure non définie"
            
            # Send to HR
            if hr_email:
                hr_subject = f" Rappel entretien dans 24h - {candidate_name}"
                hr_html = self._create_24h_reminder_html(candidate_name, job_title, company_name, interview_date, interview_time, "HR")
                hr_text = self._create_24h_reminder_text(candidate_name, job_title, company_name, interview_date, interview_time, "HR")
                self.send_email(hr_email, hr_subject, hr_html, hr_text)
            
            # Send to candidate
            if candidate_email:
                candidate_subject = f" Rappel entretien dans 24h - {job_title}"
                candidate_html = self._create_24h_reminder_html(candidate_name, job_title, company_name, interview_date, interview_time, "candidate")
                candidate_text = self._create_24h_reminder_text(candidate_name, job_title, company_name, interview_date, interview_time, "candidate")
                self.send_email(candidate_email, candidate_subject, candidate_html, candidate_text)
            
            db.close()
            return True
            
        except Exception as e:
            print(f"ERROR: Error sending 24h reminder: {e}")
            db.close()
            return False

    def send_20min_hr_reminder(self, application_id: int):
        """Send 20-minute reminder to HR"""
        try:
            db = SessionLocal()
            application = db.query(Application).filter(Application.id == application_id).first()
            if not application:
                db.close()
                return False
            
            candidate_name = application.candidate_profile.name if application.candidate_profile else "Candidat"
            job_title = application.job.title if application.job else "Poste"
            
            hr_admin = db.query(HRAdmin).first()
            hr_email = hr_admin.email if hr_admin else None
            
            if not hr_email:
                return False
            
            subject = f" Entretien dans 20 minutes - {candidate_name}"
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Rappel entretien</title>
            </head>
            <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8fafc;">
                <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                    <!-- Header -->
                    <div style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); padding: 2rem; text-align: center;">
                        <h1 style="color: white; margin: 0; font-size: 1.5rem;">
 CV Analyzer Pro
                        </h1>
                        <p style="color: #fef3c7; margin: 0.5rem 0 0 0;">Rappel entretien</p>
                    </div>
                    
                    <!-- Content -->
                    <div style="padding: 2rem;">
                        <h2 style="color: #1e293b; margin-bottom: 1rem;">Entretien dans 20 minutes !</h2>
                        
                        <div style="background: #fef3c7; border: 1px solid #f59e0b; border-radius: 8px; padding: 1.5rem; margin: 1.5rem 0;">
                            <h3 style="color: #92400e; margin: 0 0 1rem 0;"> Entretien imminent</h3>
                            <p style="color: #92400e; margin: 0.5rem 0;"><strong>Candidat:</strong> {candidate_name}</p>
                            <p style="color: #92400e; margin: 0.5rem 0;"><strong>Poste:</strong> {job_title}</p>
                        </div>
                        
                        <p style="color: #64748b; line-height: 1.6;">
                            Votre entretien avec <strong>{candidate_name}</strong> commence dans 20 minutes. 
                            Préparez-vous et vérifiez votre environnement de travail.
                        </p>
                        
                        <div style="background: #fef2f2; border-left: 4px solid #ef4444; padding: 1rem; border-radius: 0 8px 8px 0; margin: 1.5rem 0;">
                            <p style="color: #dc2626; margin: 0; font-size: 0.9rem;">
                                <strong> Lien de réunion :</strong> Vous recevrez le lien Zoom dans 15 minutes (5 minutes avant l'entretien).
                            </p>
                        </div>
                    </div>
                    
                    <!-- Footer -->
                    <div style="background: #f1f5f9; padding: 1.5rem; text-align: center; border-top: 1px solid #e2e8f0;">
                        <p style="color: #64748b; margin: 0; font-size: 0.9rem;">
                            © 2024 CV Analyzer Pro. Tous droits réservés.
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            text_content = f"""
            Bonjour,
            
            Votre entretien avec {candidate_name} pour le poste de {job_title} commence dans 20 minutes.
            
            Préparez-vous et vérifiez votre environnement de travail.
            Vous recevrez le lien Zoom dans 15 minutes.
            
            Cordialement,
            L'équipe CV Analyzer Pro
            """
            
            result = self.send_email(hr_email, subject, html_content, text_content)
            db.close()
            return result
            
        except Exception as e:
            print(f"ERROR: Error sending 20min HR reminder: {e}")
            db.close()
            return False

    def send_15min_candidate_reminder(self, application_id: int):
        """Send 15-minute reminder to candidate to get ready"""
        try:
            db = SessionLocal()
            application = db.query(Application).filter(Application.id == application_id).first()
            if not application:
                db.close()
                return False
            
            candidate_name = application.candidate_profile.name if application.candidate_profile else "Candidat"
            candidate_email = application.candidate_profile.contact.email if application.candidate_profile and application.candidate_profile.contact else None
            
            if not candidate_email:
                return False
            
            job_title = application.job.title if application.job else "Poste"
            company_name = application.job.company.company_name if application.job and application.job.company else "Entreprise"
            
            subject = f" Entretien dans 15 minutes - Préparez-vous !"
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Préparez-vous pour votre entretien</title>
            </head>
            <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8fafc;">
                <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                    <!-- Header -->
                    <div style="background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%); padding: 2rem; text-align: center;">
                        <h1 style="color: white; margin: 0; font-size: 1.5rem;">
 CV Analyzer Pro
                        </h1>
                        <p style="color: #e0e7ff; margin: 0.5rem 0 0 0;">Préparez-vous !</p>
                    </div>
                    
                    <!-- Content -->
                    <div style="padding: 2rem;">
                        <h2 style="color: #1e293b; margin-bottom: 1rem;">Entretien dans 15 minutes !</h2>
                        
                        <div style="background: #eff6ff; border: 1px solid #3b82f6; border-radius: 8px; padding: 1.5rem; margin: 1.5rem 0;">
                            <h3 style="color: #1e40af; margin: 0 0 1rem 0;"> Votre entretien</h3>
                            <p style="color: #1e40af; margin: 0.5rem 0;"><strong>Poste:</strong> {job_title}</p>
                            <p style="color: #1e40af; margin: 0.5rem 0;"><strong>Entreprise:</strong> {company_name}</p>
                        </div>
                        
                        <h3 style="color: #1e293b; margin-bottom: 1rem;"> Checklist de préparation :</h3>
                        <ul style="color: #64748b; line-height: 1.8; margin: 0; padding-left: 1.5rem;">
                            <li>Vérifiez votre connexion internet</li>
                            <li>Testez votre micro et votre caméra</li>
                            <li>Préparez un environnement calme et professionnel</li>
                            <li>Ayez votre CV et vos questions à portée de main</li>
                            <li>Habillez-vous de manière professionnelle</li>
                        </ul>
                        
                        <div style="background: #f0fdf4; border-left: 4px solid #10b981; padding: 1rem; border-radius: 0 8px 8px 0; margin: 1.5rem 0;">
                            <p style="color: #166534; margin: 0; font-size: 0.9rem;">
                                <strong> Lien de réunion :</strong> Vous recevrez le lien Zoom dans 5 minutes, au début de l'entretien.
                            </p>
                        </div>
                        
                        <p style="color: #64748b; line-height: 1.6; margin-top: 1.5rem;">
                            <strong>Bonne chance !</strong> Vous êtes bien préparé(e), tout va bien se passer ! 🍀
                        </p>
                    </div>
                    
                    <!-- Footer -->
                    <div style="background: #f1f5f9; padding: 1.5rem; text-align: center; border-top: 1px solid #e2e8f0;">
                        <p style="color: #64748b; margin: 0; font-size: 0.9rem;">
                            © 2024 CV Analyzer Pro. Tous droits réservés.
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            text_content = f"""
            Bonjour {candidate_name},
            
            Votre entretien pour le poste de {job_title} chez {company_name} commence dans 15 minutes !
            
            Checklist de préparation :
            - Vérifiez votre connexion internet
            - Testez votre micro et votre caméra
            - Préparez un environnement calme et professionnel
            - Ayez votre CV et vos questions à portée de main
            - Habillez-vous de manière professionnelle
            
            Vous recevrez le lien Zoom dans 5 minutes.
            
            Bonne chance !
            L'équipe CV Analyzer Pro
            """
            
            result = self.send_email(candidate_email, subject, html_content, text_content)
            db.close()
            return result
            
        except Exception as e:
            print(f"ERROR: Error sending 15min candidate reminder: {e}")
            db.close()
            return False

    def send_5min_hr_meeting_link(self, application_id: int):
        """Send meeting link to HR 5 minutes before meeting"""
        try:
            db = SessionLocal()
            application = db.query(Application).filter(Application.id == application_id).first()
            if not application:
                db.close()
                return False
            
            candidate_name = application.candidate_profile.name if application.candidate_profile else "Candidat"
            job_title = application.job.title if application.job else "Poste"
            
            hr_admin = db.query(HRAdmin).first()
            hr_email = hr_admin.email if hr_admin else None
            
            if not hr_email:
                db.close()
                return False
            
            # Create absolute URL for the Zoom meeting setup page
            base_url = os.getenv("BASE_URL", "http://localhost:8000")
            meeting_link = f"{base_url}/api/hr/interview-slots/zoom-meeting-setup?application_id={application_id}&admin_id={hr_admin.id}"
            
            subject = f" Lien de réunion - Entretien avec {candidate_name}"
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Lien de réunion</title>
            </head>
            <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8fafc;">
                <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                    <!-- Header -->
                    <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 2rem; text-align: center;">
                        <h1 style="color: white; margin: 0; font-size: 1.5rem;">
 CV Analyzer Pro
                        </h1>
                        <p style="color: #d1fae5; margin: 0.5rem 0 0 0;">Lien de réunion</p>
                    </div>
                    
                    <!-- Content -->
                    <div style="padding: 2rem;">
                        <h2 style="color: #1e293b; margin-bottom: 1rem;">Entretien dans 5 minutes !</h2>
                        
                        <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 1.5rem; margin: 1.5rem 0;">
                            <h3 style="color: #166534; margin: 0 0 1rem 0;"> Détails de l'entretien</h3>
                            <p style="color: #166534; margin: 0.5rem 0;"><strong>Candidat:</strong> {candidate_name}</p>
                            <p style="color: #166534; margin: 0.5rem 0;"><strong>Poste:</strong> {job_title}</p>
                        </div>
                        
                        <div style="text-align: center; margin: 2rem 0;">
                            <a href="{meeting_link}" 
                               style="display: inline-block; background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%); 
                                      color: white; text-decoration: none; padding: 1rem 2rem; border-radius: 8px; 
                                      font-weight: 600; font-size: 1rem;">
 Rejoindre la réunion Zoom
                            </a>
                        </div>
                        
                        <div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 1rem; border-radius: 0 8px 8px 0; margin: 1.5rem 0;">
                            <p style="color: #92400e; margin: 0; font-size: 0.9rem;">
                                <strong>💡 Conseil :</strong> Cliquez sur le lien ci-dessus pour rejoindre la réunion Zoom. 
                                Assurez-vous que votre micro et votre caméra fonctionnent correctement.
                            </p>
                        </div>
                    </div>
                    
                    <!-- Footer -->
                    <div style="background: #f1f5f9; padding: 1.5rem; text-align: center; border-top: 1px solid #e2e8f0;">
                        <p style="color: #64748b; margin: 0; font-size: 0.9rem;">
                            © 2024 CV Analyzer Pro. Tous droits réservés.
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            text_content = f"""
            Bonjour,
            
            Votre entretien avec {candidate_name} pour le poste de {job_title} commence dans 5 minutes !
            
            Lien de réunion Zoom : {meeting_link}
            
            Cliquez sur le lien pour rejoindre la réunion.
            
            Cordialement,
            L'équipe CV Analyzer Pro
            """
            
            result = self.send_email(hr_email, subject, html_content, text_content)
            db.close()
            return result
            
        except Exception as e:
            print(f"ERROR: Error sending 5min HR meeting link: {e}")
            db.close()
            return False

    def send_meeting_time_candidate_link(self, application_id: int):
        """Send meeting link to candidate at meeting time"""
        try:
            db = SessionLocal()
            application = db.query(Application).filter(Application.id == application_id).first()
            if not application:
                db.close()
                return False
            
            candidate_name = application.candidate_profile.name if application.candidate_profile else "Candidat"
            candidate_email = application.candidate_profile.contact.email if application.candidate_profile and application.candidate_profile.contact else None
            
            if not candidate_email:
                return False
            
            job_title = application.job.title if application.job else "Poste"
            company_name = application.job.company.company_name if application.job and application.job.company else "Entreprise"
            
            # Get the actual meeting link from the database
            meeting_link = application.google_meet_link or "https://zoom.com"
            
            subject = f" Votre entretien commence maintenant - {company_name}"
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Votre entretien commence</title>
            </head>
            <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8fafc;">
                <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                    <!-- Header -->
                    <div style="background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%); padding: 2rem; text-align: center;">
                        <h1 style="color: white; margin: 0; font-size: 1.5rem;">
 CV Analyzer Pro
                        </h1>
                        <p style="color: #e0e7ff; margin: 0.5rem 0 0 0;">C'est parti !</p>
                    </div>
                    
                    <!-- Content -->
                    <div style="padding: 2rem;">
                        <h2 style="color: #1e293b; margin-bottom: 1rem;">Votre entretien commence maintenant !</h2>
                        
                        <div style="background: #eff6ff; border: 1px solid #3b82f6; border-radius: 8px; padding: 1.5rem; margin: 1.5rem 0;">
                            <h3 style="color: #1e40af; margin: 0 0 1rem 0;"> Détails de l'entretien</h3>
                            <p style="color: #1e40af; margin: 0.5rem 0;"><strong>Poste:</strong> {job_title}</p>
                            <p style="color: #1e40af; margin: 0.5rem 0;"><strong>Entreprise:</strong> {company_name}</p>
                        </div>
                        
                        <div style="text-align: center; margin: 2rem 0;">
                            <a href="{meeting_link}" 
                               style="display: inline-block; background: linear-gradient(135deg, #10b981 0%, #059669 100%); 
                                      color: white; text-decoration: none; padding: 1rem 2rem; border-radius: 8px; 
                                      font-weight: 600; font-size: 1rem;">
                                🚀 Rejoindre l'entretien maintenant
                            </a>
                        </div>
                        
                        <div style="background: #f0fdf4; border-left: 4px solid #10b981; padding: 1rem; border-radius: 0 8px 8px 0; margin: 1.5rem 0;">
                            <p style="color: #166534; margin: 0; font-size: 0.9rem;">
                                <strong>💡 Conseil :</strong> Cliquez sur le bouton ci-dessus pour rejoindre votre entretien Zoom. 
                                Assurez-vous que votre micro et votre caméra sont activés.
                            </p>
                        </div>
                        
                        <p style="color: #64748b; line-height: 1.6; margin-top: 1.5rem;">
                            <strong>Bonne chance !</strong> Montrez votre meilleur profil ! 🌟
                        </p>
                    </div>
                    
                    <!-- Footer -->
                    <div style="background: #f1f5f9; padding: 1.5rem; text-align: center; border-top: 1px solid #e2e8f0;">
                        <p style="color: #64748b; margin: 0; font-size: 0.9rem;">
                            © 2024 CV Analyzer Pro. Tous droits réservés.
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            text_content = f"""
            Bonjour {candidate_name},
            
            Votre entretien pour le poste de {job_title} chez {company_name} commence maintenant !
            
            Lien de réunion Zoom : {meeting_link}
            
            Cliquez sur le lien pour rejoindre votre entretien.
            
            Bonne chance !
            L'équipe CV Analyzer Pro
            """
            
            result = self.send_email(candidate_email, subject, html_content, text_content)
            db.close()
            return result
            
        except Exception as e:
            print(f"ERROR: Error sending meeting time candidate link: {e}")
            db.close()
            return False

    def _create_24h_reminder_html(self, candidate_name: str, job_title: str, company_name: str, interview_date: str, interview_time: str, recipient_type: str) -> str:
        """Create HTML content for 24h reminder"""
        if recipient_type == "HR":
            header_color = "linear-gradient(135deg, #f59e0b 0%, #d97706 100%)"
            header_text_color = "#fef3c7"
            title = "Rappel entretien dans 24h"
            content_color = "#92400e"
            bg_color = "#fef3c7"
            border_color = "#f59e0b"
        else:
            header_color = "linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)"
            header_text_color = "#e0e7ff"
            title = "Rappel entretien dans 24h"
            content_color = "#1e40af"
            bg_color = "#eff6ff"
            border_color = "#3b82f6"
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Rappel entretien</title>
        </head>
        <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8fafc;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                <!-- Header -->
                <div style="background: {header_color}; padding: 2rem; text-align: center;">
                    <h1 style="color: white; margin: 0; font-size: 1.5rem;">
 CV Analyzer Pro
                    </h1>
                    <p style="color: {header_text_color}; margin: 0.5rem 0 0 0;">{title}</p>
                </div>
                
                <!-- Content -->
                <div style="padding: 2rem;">
                    <h2 style="color: #1e293b; margin-bottom: 1rem;">Entretien dans 24 heures !</h2>
                    
                    <div style="background: {bg_color}; border: 1px solid {border_color}; border-radius: 8px; padding: 1.5rem; margin: 1.5rem 0;">
                        <h3 style="color: {content_color}; margin: 0 0 1rem 0;"> Détails de l'entretien</h3>
                        <p style="color: {content_color}; margin: 0.5rem 0;"><strong>Candidat:</strong> {candidate_name}</p>
                        <p style="color: {content_color}; margin: 0.5rem 0;"><strong>Poste:</strong> {job_title}</p>
                        <p style="color: {content_color}; margin: 0.5rem 0;"><strong>Entreprise:</strong> {company_name}</p>
                        <p style="color: {content_color}; margin: 0.5rem 0;"><strong>Date:</strong> {interview_date}</p>
                        <p style="color: {content_color}; margin: 0.5rem 0;"><strong>Heure:</strong> {interview_time}</p>
                    </div>
                    
                    <p style="color: #64748b; line-height: 1.6;">
                        {"Votre entretien avec" if recipient_type == "HR" else "Votre entretien pour"} <strong>{candidate_name if recipient_type == "HR" else job_title}</strong> 
                        {"commence dans 24 heures. Préparez-vous et vérifiez votre environnement de travail." if recipient_type == "HR" else "chez " + company_name + " commence dans 24 heures. Préparez-vous bien !"}
                    </p>
                </div>
                
                <!-- Footer -->
                <div style="background: #f1f5f9; padding: 1.5rem; text-align: center; border-top: 1px solid #e2e8f0;">
                    <p style="color: #64748b; margin: 0; font-size: 0.9rem;">
                        © 2024 CV Analyzer Pro. Tous droits réservés.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """

    def _create_24h_reminder_text(self, candidate_name: str, job_title: str, company_name: str, interview_date: str, interview_time: str, recipient_type: str) -> str:
        """Create text content for 24h reminder"""
        if recipient_type == "HR":
            return f"""
            Bonjour,
            
            Votre entretien avec {candidate_name} pour le poste de {job_title} commence dans 24 heures.
            
            Détails :
            - Candidat: {candidate_name}
            - Poste: {job_title}
            - Entreprise: {company_name}
            - Date: {interview_date}
            - Heure: {interview_time}
            
            Préparez-vous et vérifiez votre environnement de travail.
            
            Cordialement,
            L'équipe CV Analyzer Pro
            """
        else:
            return f"""
            Bonjour {candidate_name},
            
            Votre entretien pour le poste de {job_title} chez {company_name} commence dans 24 heures !
            
            Détails :
            - Poste: {job_title}
            - Entreprise: {company_name}
            - Date: {interview_date}
            - Heure: {interview_time}
            
            Préparez-vous bien !
            
            Cordialement,
            L'équipe CV Analyzer Pro
            """


# Background task scheduler for interview notifications
class InterviewNotificationScheduler:
    def __init__(self):
        self.notification_service = InterviewNotificationService()
    
    async def schedule_interview_notifications(self, application_id: int):
        """Schedule all interview notifications for an application"""
        try:
            db = SessionLocal()
            application = db.query(Application).filter(Application.id == application_id).first()
            
            if not application or not application.interview_date:
                print(f"ERROR: No interview date found for application {application_id}")
                return
            
            interview_datetime = application.interview_date
            
            # Schedule notifications
            await self._schedule_notification(
                application_id, 
                interview_datetime - timedelta(hours=24),
                "24h_reminder"
            )
            
            await self._schedule_notification(
                application_id,
                interview_datetime - timedelta(minutes=20),
                "20min_hr_reminder"
            )
            
            await self._schedule_notification(
                application_id,
                interview_datetime - timedelta(minutes=15),
                "15min_candidate_reminder"
            )
            
            await self._schedule_notification(
                application_id,
                interview_datetime - timedelta(minutes=5),
                "5min_hr_meeting_link"
            )
            
            await self._schedule_notification(
                application_id,
                interview_datetime,
                "meeting_time_candidate_link"
            )
            
            print(f" All notifications scheduled for application {application_id}")
            
        except Exception as e:
            print(f"ERROR: Error scheduling notifications: {e}")
        finally:
            db.close()
    
    async def _schedule_notification(self, application_id: int, scheduled_time: datetime, notification_type: str):
        """Schedule a single notification"""
        try:
            # Calculate delay in seconds
            now = datetime.now()
            delay = (scheduled_time - now).total_seconds()
            
            if delay > 0:
                print(f" Scheduling {notification_type} for application {application_id} in {delay/3600:.1f} hours")
                
                # Schedule the notification
                asyncio.create_task(self._send_scheduled_notification(application_id, delay, notification_type))
            else:
                print(f"⚠️ Skipping {notification_type} for application {application_id} - time has passed")
                
        except Exception as e:
            print(f"ERROR: Error scheduling {notification_type}: {e}")
    
    async def _send_scheduled_notification(self, application_id: int, delay: float, notification_type: str):
        """Send a scheduled notification after delay"""
        try:
            await asyncio.sleep(delay)
            
            db = SessionLocal()
            
            if notification_type == "24h_reminder":
                self.notification_service.send_24h_reminder(application_id, db)
            elif notification_type == "20min_hr_reminder":
                self.notification_service.send_20min_hr_reminder(application_id, db)
            elif notification_type == "15min_candidate_reminder":
                self.notification_service.send_15min_candidate_reminder(application_id, db)
            elif notification_type == "5min_hr_meeting_link":
                self.notification_service.send_5min_hr_meeting_link(application_id, db)
            elif notification_type == "meeting_time_candidate_link":
                self.notification_service.send_meeting_time_candidate_link(application_id, db)
            
            print(f" Sent {notification_type} for application {application_id}")
            
        except Exception as e:
            print(f"ERROR: Error sending scheduled notification {notification_type}: {e}")
        finally:
            db.close()
