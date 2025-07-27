import os
import sys
import logging
import cv2
import torch
import numpy as np
from datetime import datetime, timezone, timedelta
from flask import Flask, render_template, request, jsonify, redirect, url_for, make_response, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit
from flask_mail import Mail, Message
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import timezone
import speech_recognition as sr
from deepface import DeepFace
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import subprocess
import json
import re
import pdfkit
import matplotlib
matplotlib.use('Agg')  # Utiliser le backend non-interactif
import matplotlib.pyplot as plt
import uuid
import io


# Essayer plusieurs chemins possibles pour FFmpeg
possible_ffmpeg_paths = [
    r"C:\ffmpeg-7.1.1-essentials_build\bin",
    r"C:\ffmpeg\bin",
    r"C:\Program Files\ffmpeg\bin", 
    r"C:\Program Files (x86)\ffmpeg\bin",
    r"C:\Users\MSI\Downloads\ffmpeg\bin",
    r"C:\Users\MSI\Desktop\ffmpeg\bin"
]

# Ajouter les chemins possibles au PATH
for path in possible_ffmpeg_paths:
    if os.path.exists(path):
        os.environ["PATH"] += os.pathsep + path
        print(f"✅ Chemin FFmpeg ajouté: {path}")

# Check ffmpeg availability
def check_ffmpeg():
    try:
        result = subprocess.run(['ffmpeg', '-version'],
                               capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ FFmpeg trouvé et fonctionnel")
            return True
        else:
            print("❌ FFmpeg trouvé mais erreur:", result.stderr)
            return False
    except FileNotFoundError:
        print("❌ FFmpeg non trouvé dans le PATH")
        return False
    except Exception as e:
        print(f"❌ Erreur lors de la vérification de FFmpeg: {e}")
        return False

ffmpeg_available = check_ffmpeg()

app = Flask(__name__)

# Configuration de la connexion MySQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/mon_projet_flask'  # Remplacez 'your_password'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configuration Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'nour.hasni02@gmail.com'
app.config['MAIL_PASSWORD'] = 'ithyrphenumuusug'  # Remplacez par votre mot de passe d'application
app.config['SECRET_KEY'] = 'a0316815ed2f6a7ffc92305a7e95699f82f86183c09ba037'

# Initialisation des extensions
mail = Mail(app)
db = SQLAlchemy(app)
socketio = SocketIO(app, async_mode='threading')

# Initialisation du recognizer pour la transcription
recognizer = sr.Recognizer()

# Charger le modèle et le tokenizer de sentiment multilingue
model_name = "cardiffnlp/twitter-xlm-roberta-base-sentiment"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)
SENTIMENT_LABELS = ['negative', 'neutral', 'positive']

def analyze_sentiment_text(text):
    import re
    sentences = re.split(r'[.!?\n]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    all_scores = []
    for sent in sentences:
        inputs = tokenizer(sent, return_tensors="pt", truncation=True, padding=True)
        with torch.no_grad():
            outputs = model(**inputs)
            logits = outputs.logits[0]
            probs = torch.nn.functional.softmax(logits, dim=0).numpy()
        scores = {label: float(prob) for label, prob in zip(SENTIMENT_LABELS, probs)}
        all_scores.append(scores)
    # Moyenne des scores pour chaque sentiment
    avg_scores = {label: 0.0 for label in SENTIMENT_LABELS}
    for scores in all_scores:
        for label in SENTIMENT_LABELS:
            avg_scores[label] += scores[label]
    n = len(all_scores)
    if n > 0:
        for label in SENTIMENT_LABELS:
            avg_scores[label] = round((avg_scores[label] / n) * 100, 2)
    return avg_scores

# Charger le pipeline HuggingFace pour l'émotion vocale (à faire une seule fois)
audio_emotion_pipeline = pipeline(
    "audio-classification",
    model="superb/hubert-large-superb-er"
)

def analyze_audio_emotion(audio_path):
    """
    Analyse un fichier audio et retourne les émotions détectées.
    """
    if not ffmpeg_available:
        print("⚠️ FFmpeg non disponible, utilisation de données de test")
        # Retourner des données de test si ffmpeg n'est pas disponible
        return [
            {'label': 'happy', 'score': 75.5},
            {'label': 'calm', 'score': 60.2},
            {'label': 'neutral', 'score': 45.8}
        ]
    
    try:
        results = audio_emotion_pipeline(audio_path)
        # On retourne les 3 émotions principales
        return sorted(results, key=lambda x: x['score'], reverse=True)[:3]
    except Exception as e:
        print(f"Erreur lors de l'analyse audio avec ffmpeg: {e}")
        # Retourner des données de test en cas d'erreur
        return [
            {'label': 'neutral', 'score': 50.0},
            {'label': 'calm', 'score': 30.0},
            {'label': 'happy', 'score': 20.0}
        ]

# Modèles de données
class Company(db.Model):
    __tablename__ = 'company'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    region = db.Column(db.String(50))
    created_at = db.Column(db.DateTime)

    def __repr__(self):
        return f'<Company {self.name}>'

class Job(db.Model):
    __tablename__ = 'job'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(100), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=True)
    region = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    recruiter_email = db.Column(db.String(120))

    def __repr__(self):
        return f'<Job {self.title}>'

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    region = db.Column(db.String(50))
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=True)

    def __repr__(self):
        return f'<User {self.name}>'

class TimeSlot(db.Model):
    __tablename__ = 'time_slots'
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    is_booked = db.Column(db.Boolean, default=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending', nullable=False)
    meet_link = db.Column(db.String(255))
    transcription = db.Column(db.Text)
    sentiment_scores = db.Column(db.Text) # Nouveau champ pour les scores de sentiment
    sentiment_decision = db.Column(db.String(50)) # Nouveau champ pour la décision de sentiment

    def __repr__(self):
        return f'<TimeSlot {self.start_time} - {self.end_time}, Status: {self.status}>'

# Fonction pour transcrire l'audio en temps réel
def transcribe_audio(slot_id):
    with app.app_context():
        slot = TimeSlot.query.get(slot_id)
        if not slot:
            logging.error(f"Créneau {slot_id} non trouvé")
            return

        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source)
            while True:
                try:
                    audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
                    text = recognizer.recognize_google(audio, language='fr-FR')
                    slot.transcription = (slot.transcription or '') + text + '\n'
                    db.session.commit()
                    socketio.emit('transcription_update', {'slot_id': slot_id, 'text': text})
                    logging.info(f"Transcription ajoutée pour slot {slot_id}: {text}")
                except sr.WaitTimeoutError:
                    continue
                except sr.UnknownValueError:
                    logging.warning("Audio non compris")
                except sr.RequestError as e:
                    logging.error(f"Erreur de service de transcription: {e}")
                    break

# Fonction pour vérifier les entretiens
def run_with_context():
    with app.app_context():
        check_upcoming_interviews()

def check_upcoming_interviews():
    now = datetime.now(timezone('Africa/Tunis'))
    logging.info(f"Vérification des entretiens à {now}")
    upcoming = TimeSlot.query.filter(
        TimeSlot.status == 'pending',
        TimeSlot.start_time <= now + timedelta(minutes=10),
        TimeSlot.start_time >= now
    ).all()
    logging.info(f"Nombre de créneaux à venir trouvés : {len(upcoming)}")
    if not upcoming:
        logging.info("Aucun entretien approchant détecté dans la plage %s à %s", now, now + timedelta(minutes=10))
        return
    recruiter_email = "nour.hasni@esprit.tn"
    for slot in upcoming:
        user = User.query.get(slot.user_id)
        if not user:
            logging.info(f"Utilisateur non trouvé pour le créneau à {slot.start_time}")
            continue
        meet_room_name = f"entretien_{slot.id}_{uuid.uuid4().hex[:8]}"
        meet_link = url_for('interview', slot_id=slot.id, meet_room_name=meet_room_name, user_name=user.name, _external=True)
        slot.meet_link = meet_link
        db.session.commit()
        logging.info(f"Lien Jitsi généré : {meet_link}")
        try:
            msg_candidate = Message('Invitation à votre entretien',
                                   sender=app.config['MAIL_USERNAME'],
                                   recipients=[user.email])
            msg_candidate.body = f"Bonjour {user.name},\n\nVotre entretien est prévu à {slot.start_time}. Cliquez sur ce lien pour rejoindre : {meet_link}\n\nCordialement,\nL'équipe RH"
            mail.send(msg_candidate)
            logging.info(f"E-mail envoyé à {user.email} pour l'entretien à {slot.start_time}")
        except Exception as e:
            logging.error(f"Erreur lors de l'envoi à {user.email}: {str(e)}", exc_info=True)
        try:
            msg_recruiter = Message('Nouvel entretien à superviser',
                                   sender=app.config['MAIL_USERNAME'],
                                   recipients=[recruiter_email])
            msg_recruiter.body = f"Bonjour,\n\nUn entretien avec {user.name} est prévu à {slot.start_time}. Lien : {meet_link}\n\nCordialement,\nL'équipe RH"
            mail.send(msg_recruiter)
            logging.info(f"E-mail envoyé à {recruiter_email} pour l'entretien à {slot.start_time}")
        except Exception as e:
            logging.error(f"Erreur lors de l'envoi à {recruiter_email}: {str(e)}", exc_info=True)

# Routes
@app.route('/')
def accueil():
    return render_template('accueil.html')

@app.route('/index')
def index():
    companies = Company.query.all()
    jobs = Job.query.all()
    return render_template('index.html', companies=companies, jobs=jobs)

@app.route('/add_user', methods=['POST'])
def add_user():
    name = request.form['name']
    email = request.form['email']
    company_id = request.form.get('company_id')
    job_id = request.form.get('job_id')
    phone = request.form.get('phone')
    region = request.form.get('region')

    try:
        new_user = User(name=name, email=email, company_id=company_id, job_id=job_id, phone=phone, region=region)
        db.session.add(new_user)
        db.session.commit()
        logging.info(f"Utilisateur créé : {name} ({email})")

        # Send confirmation email to candidate
        try:
            msg_candidate = Message('Confirmation de votre inscription',
                                   sender=app.config['MAIL_USERNAME'],
                                   recipients=[email])
            msg_candidate.body = f"Bonjour {name},\n\nVotre inscription a été reçue avec succès. Veuillez choisir un créneau pour votre entretien sur la page suivante.\n\nCordialement,\nL'équipe RH"
            mail.send(msg_candidate)
            logging.info(f"E-mail de confirmation envoyé à {email}")
        except Exception as e:
            logging.error(f"Erreur lors de l'envoi de l'e-mail à {email}: {str(e)}", exc_info=True)
            # Continue even if email fails to avoid blocking user creation
    except Exception as e:
        logging.error(f"Erreur lors de la création de l'utilisateur: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': f"Erreur lors de l'inscription: {str(e)}"}), 500

    return redirect(url_for('calendar', user_id=new_user.id))

@app.route('/calendar/<int:user_id>')
def calendar(user_id):
    return render_template('calendar.html', user_id=user_id)

@app.route('/interview/<int:slot_id>/<meet_room_name>/<user_name>')
def interview(slot_id, meet_room_name, user_name):
    return render_template('interview.html', slot_id=slot_id, meet_room_name=meet_room_name, user_name=user_name)

@app.route('/api/slots', methods=['GET'])
def get_slots():
    today = datetime.now(timezone('Africa/Tunis'))
    end_date = today + timedelta(days=90)

    booked_slots = {(slot.start_time, slot.end_time): slot.id for slot in TimeSlot.query.all()}

    events = []
    current_date = today.date()
    while current_date <= end_date.date():
        if current_date.weekday() < 5:
            current_time = datetime.combine(current_date, datetime.strptime('08:00', '%H:%M').time())
            end_time = datetime.combine(current_date, datetime.strptime('17:30', '%H:%M').time())

            while current_time < end_time:
                start_slot = current_time
                end_slot = start_slot + timedelta(minutes=30)
                slot_key = (start_slot, end_slot)

                if slot_key in booked_slots:
                    events.append({
                        'id': booked_slots[slot_key],
                        'title': 'Réservé',
                        'start': start_slot.isoformat(),
                        'end': end_slot.isoformat(),
                        'backgroundColor': '#2196F3',
                        'borderColor': '#2196F3'
                    })
                else:
                    events.append({
                        'id': f"dynamic_{start_slot.isoformat()}",
                        'title': 'Disponible',
                        'start': start_slot.isoformat(),
                        'end': end_slot.isoformat(),
                        'backgroundColor': '#4CAF50',
                        'borderColor': '#4CAF50'
                    })
                current_time += timedelta(minutes=30)

        current_date += timedelta(days=1)

    return jsonify(events)

@app.route('/book_slot', methods=['POST'])
def book_slot():
    data = request.get_json()
    slot_id = data.get('slot_id')
    user_id = data.get('user_id')
    recruiter_email = "nour.hasni@esprit.tn"

    now = datetime.now(timezone('Africa/Tunis'))
    pending_slot = TimeSlot.query.filter(
        TimeSlot.user_id == user_id,
        TimeSlot.status == 'pending',
        TimeSlot.end_time > now
    ).first()

    if pending_slot:
        return jsonify({'success': False, 'message': 'Vous avez déjà un entretien à venir en attente.'}), 400

    with app.app_context():
        if slot_id.startswith('dynamic_'):
            start_time_str = slot_id.replace('dynamic_', '')
            start_time = datetime.fromisoformat(start_time_str)
            end_time = start_time + timedelta(minutes=30)

            existing_slot = TimeSlot.query.filter_by(start_time=start_time, end_time=end_time).first()
            if existing_slot:
                return jsonify({'success': False, 'message': 'Créneau déjà réservé.'}), 400

            new_slot = TimeSlot(start_time=start_time, end_time=end_time, user_id=user_id, status='pending')
            db.session.add(new_slot)
            db.session.commit()

            # Generate Jitsi meet link
            user = User.query.get(user_id)
            if not user:
                logging.error(f"Utilisateur {user_id} non trouvé")
                return jsonify({'success': False, 'message': 'Utilisateur non trouvé.'}), 400

            meet_room_name = f"entretien_{new_slot.id}_{uuid.uuid4().hex[:8]}"
            meet_link = url_for('interview', slot_id=new_slot.id, meet_room_name=meet_room_name, user_name=user.name, _external=True)
            new_slot.meet_link = meet_link
            db.session.commit()
            logging.info(f"Lien Jitsi généré pour slot {new_slot.id}: {meet_link}")

            # Send email to candidate
            try:
                msg_candidate = Message('Confirmation de votre entretien',
                                       sender=app.config['MAIL_USERNAME'],
                                       recipients=[user.email])
                msg_candidate.body = f"Bonjour {user.name},\n\nVotre entretien est confirmé pour le {start_time}. Cliquez sur ce lien pour rejoindre : {meet_link}\n\nCordialement,\nL'équipe RH"
                mail.send(msg_candidate)
                logging.info(f"E-mail de confirmation envoyé à {user.email} pour l'entretien à {start_time}")
            except Exception as e:
                logging.error(f"Erreur lors de l'envoi à {user.email}: {str(e)}", exc_info=True)
                return jsonify({'success': False, 'message': f"Créneau réservé, mais erreur lors de l'envoi de l'e-mail au candidat: {str(e)}"}), 400

            # Send email to recruiter
            try:
                msg_recruiter = Message('Nouvel entretien réservé',
                                       sender=app.config['MAIL_USERNAME'],
                                       recipients=[recruiter_email])
                msg_recruiter.body = f"Bonjour,\n\nUn entretien avec {user.name} a été réservé pour le {start_time}. Lien : {meet_link}\n\nCordialement,\nL'équipe RH"
                mail.send(msg_recruiter)
                logging.info(f"E-mail de notification envoyé à {recruiter_email} pour l'entretien à {start_time}")
            except Exception as e:
                logging.error(f"Erreur lors de l'envoi à {recruiter_email}: {str(e)}", exc_info=True)
                return jsonify({'success': False, 'message': f"Créneau réservé, mais erreur lors de l'envoi de l'e-mail au recruteur: {str(e)}"}), 400

            return jsonify({'success': True, 'message': 'Créneau réservé avec succès et e-mails envoyés !', 'color': '#2196F3', 'id': new_slot.id})
        else:
            slot = TimeSlot.query.get(slot_id)
            if slot and not slot.is_booked and slot.status != 'pending':
                slot.is_booked = True
                slot.user_id = user_id
                slot.status = 'pending'
                db.session.commit()

                # Generate Jitsi meet link
                user = User.query.get(user_id)
                if not user:
                    logging.error(f"Utilisateur {user_id} non trouvé")
                    return jsonify({'success': False, 'message': 'Utilisateur non trouvé.'}), 400

                meet_room_name = f"entretien_{slot.id}_{uuid.uuid4().hex[:8]}"
                meet_link = url_for('interview', slot_id=slot.id, meet_room_name=meet_room_name, user_name=user.name, _external=True)
                slot.meet_link = meet_link
                db.session.commit()
                logging.info(f"Lien Jitsi généré pour slot {slot.id}: {meet_link}")

                # Send email to candidate
                try:
                    msg_candidate = Message('Confirmation de votre entretien',
                                           sender=app.config['MAIL_USERNAME'],
                                           recipients=[user.email])
                    msg_candidate.body = f"Bonjour {user.name},\n\nVotre entretien est confirmé pour le {slot.start_time}. Cliquez sur ce lien pour rejoindre : {meet_link}\n\nCordialement,\nL'équipe RH"
                    mail.send(msg_candidate)
                    logging.info(f"E-mail de confirmation envoyé à {user.email} pour l'entretien à {slot.start_time}")
                except Exception as e:
                    logging.error(f"Erreur lors de l'envoi à {user.email}: {str(e)}", exc_info=True)
                    return jsonify({'success': False, 'message': f"Créneau réservé, mais erreur lors de l'envoi de l'e-mail au candidat: {str(e)}"}), 400

                # Send email to recruiter
                try:
                    msg_recruiter = Message('Nouvel entretien réservé',
                                           sender=app.config['MAIL_USERNAME'],
                                           recipients=[recruiter_email])
                    msg_recruiter.body = f"Bonjour,\n\nUn entretien avec {user.name} a été réservé pour le {slot.start_time}. Lien : {meet_link}\n\nCordialement,\nL'équipe RH"
                    mail.send(msg_recruiter)
                    logging.info(f"E-mail de notification envoyé à {recruiter_email} pour l'entretien à {slot.start_time}")
                except Exception as e:
                    logging.error(f"Erreur lors de l'envoi à {recruiter_email}: {str(e)}", exc_info=True)
                    return jsonify({'success': False, 'message': f"Créneau réservé, mais erreur lors de l'envoi de l'e-mail au recruteur: {str(e)}"}), 400

                return jsonify({'success': True, 'message': 'Créneau réservé avec succès et e-mails envoyés !', 'color': '#2196F3'})
            else:
                return jsonify({'success': False, 'message': 'Créneau non disponible ou déjà réservé.'}), 400

@app.route('/update_status', methods=['GET'])
def update_status():
    now = datetime.now(timezone('Africa/Tunis'))
    past_slots = TimeSlot.query.filter(TimeSlot.end_time < now).all()

    for slot in past_slots:
        if slot.status == 'pending':
            slot.status = 'missed'
    db.session.commit()

    return jsonify({'success': True, 'message': 'Statuts mis à jour avec succès !'})

@app.route('/test_email')
def test_email():
    with app.app_context():
        try:
            msg = Message('Test e-mail', 
                          sender=app.config['MAIL_USERNAME'], 
                          recipients=['96414536drira@gmail.com'])
            msg.body = 'Ceci est un test d\'e-mail.'
            mail.send(msg)
            logging.info("E-mail de test envoyé à 96414536drira@gmail.com")
            return "E-mail de test envoyé, vérifie tes logs et l'inbox du destinataire !"
        except Exception as e:
            logging.error(f"Erreur lors de l'envoi de l'e-mail: {str(e)}", exc_info=True)
            return f"Erreur lors de l'envoi de l'e-mail: {str(e)}"

@app.route('/start_transcription/<int:slot_id>')
def start_transcription(slot_id):
    threading.Thread(target=transcribe_audio, args=(slot_id,), daemon=True).start()
    return jsonify({'success': True, 'message': 'Transcription démarrée'})

@app.route('/analyze_emotion', methods=['POST'])
def analyze_emotion():
    data = request.get_json()
    text = data.get('text', '')
    if not text.strip():
        return jsonify({'success': False, 'message': 'Aucun texte fourni.'}), 400
    try:
        scores = analyze_sentiment_text(text)
        return jsonify({'success': True, 'scores': scores})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/analyze_audio_emotion', methods=['POST'])
def analyze_audio_emotion_route():
    data = request.get_json()
    audio_path = data.get('audio_path')
    slot_id = data.get('slot_id')
    if not audio_path or not os.path.exists(audio_path):
        return jsonify({'success': False, 'message': 'Fichier audio non trouvé.'}), 400
    try:
        emotions = analyze_audio_emotion(audio_path)
        # Enregistre les émotions dans un log pour le rapport
        if slot_id:
            log_path = f'audio_emotions_slot_{slot_id}.log'
            with open(log_path, 'a') as f:
                for emo in emotions:
                    f.write(f"{emo['label']}: {emo['score']}\n")
        return jsonify({'success': True, 'emotions': emotions})
    except Exception as e:
        import traceback
        err_msg = f"Erreur analyse_audio_emotion: {str(e)}\n{traceback.format_exc()}"
        print(err_msg)
        import logging
        logging.error(err_msg)
        return jsonify({'success': False, 'message': err_msg}), 500

@app.route('/upload_audio', methods=['POST'])
def upload_audio():
    audio = request.files['audio']
    slot_id = request.form['slot_id']
    save_dir = "audio_uploads"
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, f"slot_{slot_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.wav")
    audio.save(save_path)
    # Ici, tu pourras lancer l’analyse HuggingFace plus tard
    return jsonify({'success': True, 'message': 'Audio reçu', 'path': save_path})

@app.route('/list_audio_files', methods=['GET'])
def list_audio_files():
    audio_dir = os.path.join(os.path.dirname(__file__), 'audio_uploads')
    if not os.path.exists(audio_dir):
        return jsonify({'files': []})
    files = [f for f in os.listdir(audio_dir) if f.endswith('.wav')]
    files = sorted(files, reverse=True)  # Les plus récents d'abord
    return jsonify({'files': files})

@app.route('/upload_face_image', methods=['POST'])
def upload_face_image():
    image_file = request.files['image']
    slot_id = request.form['slot_id']
    img_bytes = np.frombuffer(image_file.read(), np.uint8)
    img = cv2.imdecode(img_bytes, cv2.IMREAD_COLOR)
    # Analyse avec DeepFace
    result = DeepFace.analyze(img, actions=['emotion'], enforce_detection=False)
    if isinstance(result, list):
        result = result[0]
    main_emotion = result['dominant_emotion']
    emotions = result['emotion']
    # Stocke dans un fichier (ou base de données)
    with open(f'face_emotions_slot_{slot_id}.log', 'a') as f:
        f.write(f'{main_emotion}: {emotions[main_emotion]}\n')
    emotions_py = {k: float(v) for k, v in emotions.items()}
    return jsonify({'success': True, 'emotion': main_emotion, 'scores': emotions_py})

@socketio.on('connect')
def handle_connect():
    logging.info("Client connecté via SocketIO")

# Initialiser le scheduler une seule fois
scheduler = None
def init_scheduler():
    global scheduler
    if scheduler is None:
        scheduler = BackgroundScheduler()
        scheduler.add_job(run_with_context, 'interval', minutes=5)
        scheduler.start()
        logging.info("Scheduler démarré à %s", datetime.now(timezone('Africa/Tunis')))

if __name__ == '__main__':
    # Initialisation du scheduler
    scheduler = BackgroundScheduler(timezone='Europe/Paris')
    scheduler.add_job(check_upcoming_interviews, 'interval', minutes=1)
    scheduler.start()

    # Initialisation de la base de données
    with app.app_context():
        try:
            db.create_all()
            logging.info("Database tables created successfully")
        except Exception as e:
            logging.error(f"Failed to create database tables: {str(e)}", exc_info=True)
            print(f"Error: Could not connect to database - {str(e)}")
            exit(1)

    # Démarrage du serveur
    try:
        print("\n* Starting Flask application...")
        print("* Host: 0.0.0.0")
        print("* Port: 5000")
        print("* Debug mode: on")
        print("* URL: http://localhost:5000")
        socketio.run(app, host='0.0.0.0', port=5000, debug=True)
    except Exception as e:
        logging.error(f"Failed to start server: {str(e)}", exc_info=True)
        print(f"Error starting server: {str(e)}")
        exit(1)
    
    try:
        logging.info("Starting Flask-SocketIO server")
        socketio.run(app, debug=True, use_reloader=False, port=5000)
    except Exception as e:
        logging.error(f"Error starting server: {str(e)}", exc_info=True)
        scheduler.shutdown()

print("=== DEMARRAGE APP.PY ===")
print("=== ROUTES DISPONIBLES ===")
for rule in app.url_map.iter_rules():
    print(rule)

print("Route /rapport_emotions/<int:slot_id> enregistrée")
@app.route('/rapport_emotions/<int:slot_id>')
def rapport_emotions(slot_id):
    EMOJI = {
        # Émotions faciales
        'happy': '😊', 'sad': '😢', 'angry': '😠', 'neutral': '😐', 'fear': '😨', 'surprise': '😲', 'disgust': '🤢',
        # Émotions vocales
        'calm': '😌', 'frustration': '😤', 'excited': '🤩', 'boredom': '🥱', 'tired': '🥱', 'confused': '😕', 'stressed': '😬',
        'pleasure': '😃', 'pain': '😣', 'other': '❓', 'positive': '😃', 'negative': '😞',
        # Émotions audio supplémentaires
        'ang': '😠', 'neu': '😐', 'hap': '😊', 'sad': '😢', 'fru': '😤', 'exc': '🤩', 'fea': '😨', 'dis': '🤢',
        'sur': '😲', 'con': '😕', 'str': '😬', 'bor': '🥱', 'tir': '🥱', 'ple': '😃', 'pai': '😣'
    }
    print(f"DEBUG: rapport_emotions appelée avec slot_id={slot_id}")
    face_log = f'face_emotions_slot_{slot_id}.log'
    audio_log = f'audio_emotions_slot_{slot_id}.log'
    if not os.path.exists(face_log) and not os.path.exists(audio_log):
        return "<h2>Aucun rapport disponible pour ce slot.</h2><a href='/index'>Retour à l'accueil</a>", 200
    try:
        # Lecture des logs
        face_log = f'face_emotions_slot_{slot_id}.log'
        audio_log = None
        import glob
        audio_files = glob.glob(f'audio_uploads/slot_{slot_id}_*.wav')
        if audio_files:
            audio_log = f'audio_emotions_slot_{slot_id}.log'
        # Analyse faciale (compte)
        face_emotions = {}
        face_emotions_scores = {}
        if os.path.exists(face_log):
            try:
                with open(face_log, 'r') as f:
                    for line in f:
                        parts = line.strip().split(':')
                        if len(parts) == 2:
                            emo = parts[0].strip()
                            try:
                                score = float(parts[1].strip())
                            except Exception:
                                score = 1.0
                            face_emotions[emo] = face_emotions.get(emo, 0) + 1
                            face_emotions_scores[emo] = face_emotions_scores.get(emo, 0) + score
            except Exception:
                face_emotions = {}
                face_emotions_scores = {}
        else:
            face_emotions = {}
            face_emotions_scores = {}
        # Analyse audio (compte)
        audio_emotions = {}
        audio_emotions_scores = {}
        if audio_log and os.path.exists(audio_log):
            try:
                with open(audio_log, 'r') as f:
                    for line in f:
                        parts = line.strip().split(':')
                        if len(parts) == 2:
                            emo = parts[0].strip()
                            try:
                                score = float(parts[1].strip())
                            except Exception:
                                score = 1.0
                            audio_emotions[emo] = audio_emotions.get(emo, 0) + 1
                            audio_emotions_scores[emo] = audio_emotions_scores.get(emo, 0) + score
            except Exception:
                audio_emotions = {}
                audio_emotions_scores = {}
        else:
            audio_emotions = {}
            audio_emotions_scores = {}
        # Récupération de la transcription et analyse sentiment
        slot = TimeSlot.query.get(slot_id)
        transcription = None
        if slot and slot.transcription:
            transcription = slot.transcription
        text_scores = None
        if transcription and transcription.strip():
            text_scores = analyze_sentiment_text(transcription)
        # Génère un camembert pour chaque
        import matplotlib.pyplot as plt
        fig, axs = plt.subplots(1, 2, figsize=(10, 5))
        if audio_emotions:
            axs[0].pie(audio_emotions.values(), labels=audio_emotions.keys(), autopct='%1.1f%%')
            axs[0].set_title('Émotions audio')
        else:
            axs[0].text(0.5, 0.5, 'Aucune donnée audio', ha='center', va='center')
            axs[0].set_title('Émotions audio')
        if face_emotions:
            axs[1].pie(face_emotions.values(), labels=face_emotions.keys(), autopct='%1.1f%%')
            axs[1].set_title('Émotions faciales')
        else:
            axs[1].text(0.5, 0.5, 'Aucune donnée faciale', ha='center', va='center')
            axs[1].set_title('Émotions faciales')
        plt.tight_layout()
        plt.savefig('rapport_emotions.png')
        plt.close(fig)
        # Calcul des moyennes pour chaque émotion
        face_emotions_avg = {}
        for emo in face_emotions_scores:
            count = face_emotions[emo]
            if count > 0:
                face_emotions_avg[emo] = face_emotions_scores[emo] / count
        audio_emotions_avg = {}
        for emo in audio_emotions_scores:
            count = audio_emotions[emo]
            if count > 0:
                audio_emotions_avg[emo] = audio_emotions_scores[emo] / count
        # Nouvelle fonction d'affichage pour les moyennes
        def format_emotions_avg_list(avg_dict):
            if not avg_dict:
                return '<i>Aucune donnée</i>'
            total = sum(avg_dict.values())
            if total == 0:
                return '<i>Aucune donnée</i>'
            items = []
            for emo, avg in sorted(avg_dict.items(), key=lambda x: -x[1]):
                percent = (avg / total * 100) if total > 0 else 0
                emoji = EMOJI.get(emo, '')
                
                # Mapping pour les noms complets des émotions
                emotion_names = {
                    'ang': 'Angry', 'neu': 'Neutral', 'hap': 'Happy', 'sad': 'Sad',
                    'fru': 'Frustration', 'exc': 'Excited', 'fea': 'Fear', 'dis': 'Disgust',
                    'sur': 'Surprise', 'con': 'Confused', 'str': 'Stressed', 'bor': 'Boredom',
                    'tir': 'Tired', 'ple': 'Pleasure', 'pai': 'Pain'
                }
                
                # Utiliser le nom complet si disponible, sinon capitaliser l'émotion
                emotion_name = emotion_names.get(emo, emo.capitalize())
                items.append(f"<li>{emoji} <b>{emotion_name}</b> : {avg:.2f} ({percent:.1f}%)</li>")
            return '<ul style="margin-bottom:0.5em;">' + ''.join(items) + '</ul>'
        audio_list = format_emotions_avg_list(audio_emotions_avg)
        face_list = format_emotions_avg_list(face_emotions_avg)
        # Calcul de la moyenne générale positive
        positive_audio = 0
        for k in ['happy', 'calm', 'pleasure']:
            if k in audio_emotions_scores:
                positive_audio += audio_emotions_scores[k]
        total_audio = sum(audio_emotions_scores.values())
        percent_audio = (positive_audio / total_audio * 100) if total_audio > 0 else None
        positive_face = 0
        for k in ['happy', 'calm', 'pleasure']:
            if k in face_emotions_scores:
                positive_face += face_emotions_scores[k]
        total_face = sum(face_emotions_scores.values())
        percent_face = (positive_face / total_face * 100) if total_face > 0 else None
        percent_text = None
        if text_scores and 'positive' in text_scores:
            percent_text = text_scores['positive']
        # Calcul de la moyenne générale
        percent_list = [p for p in [percent_audio, percent_face, percent_text] if p is not None]
        moyenne = sum(percent_list) / len(percent_list) if percent_list else None
        # Décision
        neutral_face_percent = None
        if face_emotions_scores and 'neutral' in face_emotions_scores and sum(face_emotions_scores.values()) > 0:
            neutral_face_percent = (face_emotions_scores['neutral'] / sum(face_emotions_scores.values())) * 100
        main_sentiment = None
        if text_scores:
            sorted_scores = sorted(text_scores.items(), key=lambda x: -x[1])
            main_sentiment = sorted_scores[0][0]
        # Enregistrement de l'analyse de sentiment textuel dans la base de données
        if slot:
            if text_scores:
                slot.sentiment_scores = json.dumps(text_scores)
                slot.sentiment_decision = main_sentiment
            else:
                slot.sentiment_scores = None
                slot.sentiment_decision = None
            db.session.commit()
        if main_sentiment == 'positive':
            decision = '✅ Passé'
            decision_html = f"<div style='font-size:1.3em;margin-bottom:0.7em;'><b>Décision :</b> <span style='font-size:1.4em'>{decision}</span> <span style='font-size:1em;color:#888;'>(sentiment textuel positif)</span></div>"
        elif neutral_face_percent is not None and neutral_face_percent > 50:
            decision = '✅ Passé'
            decision_html = f"<div style='font-size:1.3em;margin-bottom:0.7em;'><b>Décision :</b> <span style='font-size:1.4em'>{decision}</span> <span style='font-size:1em;color:#888;'>(neutral facial &gt; 50%)</span></div>"
        elif moyenne is not None:
            decision = '✅ Passé' if moyenne >= 1 else '❌ Refusé'
            decision_html = f"<div style='font-size:1.3em;margin-bottom:0.7em;'><b>Décision :</b> <span style='font-size:1.4em'>{decision}</span> <span style='font-size:1em;color:#888;'>(moyenne positive : {moyenne:.1f}%)</span></div>"
        else:
            decision_html = "<div style='font-size:1.1em;color:#888;margin-bottom:0.7em;'>Décision automatique impossible (données insuffisantes).</div>"
        # Toujours définir audio_main et face_main
        audio_main = max(audio_emotions, key=audio_emotions.get) if audio_emotions else 'Aucune'
        face_main = max(face_emotions, key=face_emotions.get) if face_emotions else 'Aucune'
        resume = f"<b>Émotion audio dominante :</b> {EMOJI.get(audio_main, '')} {audio_main}. <b>Émotion faciale dominante :</b> {EMOJI.get(face_main, '')} {face_main}."
        # Affichage HTML enrichi
        if request.args.get('popup') == '1':
            return render_template(
                'rapport.html',
                slot_id=slot_id,
                decision_html=decision_html,
                resume=resume,
                audio_list=audio_list,
                face_list=face_list,
                transcription=transcription,
                text_scores=text_scores,
                audio_emotions_scores=audio_emotions_scores,
                face_emotions_scores=face_emotions_scores,
                EMOJI=EMOJI
            )
        return render_template(
            'rapport.html',
            slot_id=slot_id,
            decision_html=decision_html,
            resume=resume,
            audio_list=audio_list,
            face_list=face_list,
            transcription=transcription,
            text_scores=text_scores,
            audio_emotions_scores=audio_emotions_scores,
            face_emotions_scores=face_emotions_scores,
            EMOJI=EMOJI
        )
    except Exception as e:
        print(f"ERREUR dans rapport_emotions: {e}")
        raise

@app.route('/rapport_emotions_img/<int:slot_id>')
def rapport_emotions_img(slot_id):
    # Génère l'image PNG du rapport (pour l'embed dans la page HTML)
    face_log = f'face_emotions_slot_{slot_id}.log'
    audio_log = None
    import glob
    audio_files = glob.glob(f'audio_uploads/slot_{slot_id}_*.wav')
    if audio_files:
        audio_log = f'audio_emotions_slot_{slot_id}.log'
    face_emotions = {}
    try:
        with open(face_log, 'r') as f:
            for line in f:
                emo = line.split(':')[0].strip()
                face_emotions[emo] = face_emotions.get(emo, 0) + 1
    except Exception:
        face_emotions = {}
    audio_emotions = {}
    try:
        with open(audio_log, 'r') as f:
            for line in f:
                emo = line.split(':')[0].strip()
                audio_emotions[emo] = audio_emotions.get(emo, 0) + 1
    except Exception:
        audio_emotions = {}
    fig, axs = plt.subplots(1, 2, figsize=(10, 5))
    if audio_emotions:
        axs[0].pie(audio_emotions.values(), labels=audio_emotions.keys(), autopct='%1.1f%%')
        axs[0].set_title('Émotions audio')
    else:
        axs[0].text(0.5, 0.5, 'Aucune donnée audio', ha='center', va='center')
        axs[0].set_title('Émotions audio')
    if face_emotions:
        axs[1].pie(face_emotions.values(), labels=face_emotions.keys(), autopct='%1.1f%%')
        axs[1].set_title('Émotions faciales')
    else:
        axs[1].text(0.5, 0.5, 'Aucune donnée faciale', ha='center', va='center')
        axs[1].set_title('Émotions faciales')
    plt.tight_layout()
    plt.savefig('rapport_emotions.png')
    plt.close(fig)
    return send_file('rapport_emotions.png', mimetype='image/png')

@app.route('/rapport_emotions_pdf/<int:slot_id>')
def rapport_emotions_pdf(slot_id):
    response = rapport_emotions(slot_id)
    if isinstance(response, tuple):
        html = response[0]
    else:
        html = response
    # Générer l'image localement
    face_log = f'face_emotions_slot_{slot_id}.log'
    audio_log = f'audio_emotions_slot_{slot_id}.log'
    face_emotions = {}
    if os.path.exists(face_log):
        with open(face_log, 'r') as f:
            for line in f:
                emo = line.split(':')[0].strip()
                face_emotions[emo] = face_emotions.get(emo, 0) + 1
    audio_emotions = {}
    if os.path.exists(audio_log):
        with open(audio_log, 'r') as f:
            for line in f:
                emo = line.split(':')[0].strip()
                audio_emotions[emo] = audio_emotions.get(emo, 0) + 1
    fig, axs = plt.subplots(1, 2, figsize=(10, 5))
    if audio_emotions:
        axs[0].pie(audio_emotions.values(), labels=audio_emotions.keys(), autopct='%1.1f%%')
        axs[0].set_title('Émotions audio')
    else:
        axs[0].text(0.5, 0.5, 'Aucune donnée audio', ha='center', va='center')
        axs[0].set_title('Émotions audio')
    if face_emotions:
        axs[1].pie(face_emotions.values(), labels=face_emotions.keys(), autopct='%1.1f%%')
        axs[1].set_title('Émotions faciales')
    else:
        axs[1].text(0.5, 0.5, 'Aucune donnée faciale', ha='center', va='center')
        axs[1].set_title('Émotions faciales')
    plt.tight_layout()
    img_path = f'report_{slot_id}.png'
    plt.savefig(img_path)
    plt.close(fig)
    # Modifier le HTML pour inclure l'image localement
    html = html.replace(f'src="{url_for("rapport_emotions_img", slot_id=slot_id)}"', f'src="{img_path}"')
    try:
        config = pdfkit.configuration(wkhtmltopdf='C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe')
        pdf = pdfkit.from_string(html, False, options={'enable-local-file-access': True})
        resp = make_response(pdf)
        resp.headers['Content-Type'] = 'application/pdf'
        resp.headers['Content-Disposition'] = f'attachment; filename=rapport_emotions_slot_{slot_id}.pdf'
        return resp
    except Exception as e:
        logging.error(f"Erreur lors de la génération du PDF: {str(e)}")
        return f"Erreur lors de la génération du PDF: {str(e)}", 500
    finally:
        if os.path.exists(img_path):
            os.remove(img_path)  # Nettoyer le fichier temporaire

@app.route('/liste_rapports')
def liste_rapports():
    # Cherche tous les fichiers de log d'émotions faciales
    import glob
    logs = glob.glob('face_emotions_slot_*.log')
    slot_ids = [f.split('_')[-1].split('.')[0] for f in logs]
    slot_ids = sorted(slot_ids, key=lambda x: int(x))
    html = "<h2>Rapports disponibles</h2><ul>"
    for slot_id in slot_ids:
        html += f"<li><a href='/rapport_emotions/{slot_id}' target='_blank'>Rapport slot {slot_id}</a></li>"
    html += "</ul>"
    html += "<a href='/index'>Retour à l'accueil</a>"
    return html

@app.route('/test_rapport')
def test_rapport():
    return "Test OK"

@app.route('/test_transcription/<int:slot_id>')
def test_transcription(slot_id):
    slot = TimeSlot.query.get(slot_id)
    if slot:
        slot.transcription = "Ceci est une transcription de test. Je suis très content et motivé pour ce poste !"
        from app import analyze_sentiment_text
        slot.sentiment_scores = json.dumps(analyze_sentiment_text(slot.transcription))
        slot.sentiment_decision = 'positive'
        db.session.commit()
        return f"Transcription et analyse de test ajoutées au slot {slot_id}. <a href='/rapport_emotions/{slot_id}?popup=1'>Voir le rapport</a>"
    return "Slot non trouvé."

@app.route('/rapport_emotions_popup', methods=['POST'])
def rapport_emotions_popup():
    data = request.get_json()
    transcription = data.get('transcription', '')
    text_scores = data.get('text_scores', {})
    slot_id = data.get('slot_id', None)
    
    EMOJI = {
        'happy': '😊', 'sad': '😢', 'angry': '😠', 'neutral': '😐', 'fear': '😨', 'surprise': '😲', 'disgust': '🤢',
        'calm': '😌', 'frustration': '😤', 'excited': '🤩', 'boredom': '🥱', 'tired': '🥱', 'confused': '😕', 'stressed': '😬',
        'pleasure': '😃', 'pain': '😣', 'other': '❓', 'positive': '😃', 'negative': '😞'
    }
    
    # Récupérer les données faciales et audio du slot
    face_log = f'face_emotions_slot_{slot_id}.log' if slot_id else None
    audio_log = f'audio_emotions_slot_{slot_id}.log' if slot_id else None
    
    # DEBUG: Afficher les informations sur les fichiers
    debug_info = f"""
    <div style="background:#f0f0f0; padding:10px; margin:10px 0; border-radius:5px; font-size:0.9em;">
        <strong>DEBUG:</strong><br>
        Slot ID: {slot_id}<br>
        Fichier facial: {face_log} - Existe: {os.path.exists(face_log) if face_log else 'N/A'}<br>
        Fichier audio: {audio_log} - Existe: {os.path.exists(audio_log) if audio_log else 'N/A'}<br>
        Transcription: {len(transcription)} caractères<br>
        Text scores: {text_scores}
    </div>
    """
    
    # Analyse faciale
    face_emotions = {}
    face_emotions_scores = {}
    if face_log and os.path.exists(face_log):
        try:
            with open(face_log, 'r') as f:
                for line in f:
                    parts = line.strip().split(':')
                    if len(parts) == 2:
                        emo = parts[0].strip()
                        try:
                            score = float(parts[1].strip())
                        except Exception:
                            score = 1.0
                        face_emotions[emo] = face_emotions.get(emo, 0) + 1
                        face_emotions_scores[emo] = face_emotions_scores.get(emo, 0) + score
        except Exception:
            face_emotions = {}
            face_emotions_scores = {}
    
    # Analyse audio
    audio_emotions = {}
    audio_emotions_scores = {}
    if audio_log and os.path.exists(audio_log):
        try:
            with open(audio_log, 'r') as f:
                for line in f:
                    parts = line.strip().split(':')
                    if len(parts) == 2:
                        emo = parts[0].strip()
                        try:
                            score = float(parts[1].strip())
                        except Exception:
                            score = 1.0
                        audio_emotions[emo] = audio_emotions.get(emo, 0) + 1
                        audio_emotions_scores[emo] = audio_emotions_scores.get(emo, 0) + score
        except Exception:
            audio_emotions = {}
            audio_emotions_scores = {}
    
    # DEBUG: Ajouter les données d'émotions au debug
    debug_info += f"""
    <div style="background:#e8f4fd; padding:10px; margin:10px 0; border-radius:5px; font-size:0.9em;">
        <strong>Données émotions:</strong><br>
        Émotions faciales: {face_emotions}<br>
        Émotions audio: {audio_emotions}
    </div>
    """
    
    # Calcul des moyennes pour chaque émotion
    face_emotions_avg = {}
    for emo in face_emotions_scores:
        count = face_emotions[emo]
        if count > 0:
            face_emotions_avg[emo] = face_emotions_scores[emo] / count
    
    audio_emotions_avg = {}
    for emo in audio_emotions_scores:
        count = audio_emotions[emo]
        if count > 0:
            audio_emotions_avg[emo] = audio_emotions_scores[emo] / count
    
    # Fonction d'affichage pour les moyennes
    def format_emotions_avg_list(avg_dict, is_audio=False):
        if not avg_dict:
            return '<i>Aucune donnée</i>'
        # Si c'est pour l'audio, ne garder que les 4 labels du modèle
        if is_audio:
            filtered = {k: v for k, v in avg_dict.items() if k in ['neu', 'hap', 'ang', 'sad']}
            total = sum(filtered.values())
            if total == 0:
                return '<i>Aucune donnée</i>'
            items = []
            emotion_names = {'neu': 'Neutral', 'hap': 'Happy', 'ang': 'Angry', 'sad': 'Sad'}
            emotion_emojis = {'neu': '😐', 'hap': '😊', 'ang': '😠', 'sad': '😢'}
            for emo, avg in sorted(filtered.items(), key=lambda x: -x[1]):
                percent = (avg / total * 100) if total > 0 else 0
                emoji = emotion_emojis.get(emo, '')
                name = emotion_names.get(emo, emo)
                items.append(f"<li>{emoji} <b>{name}</b> : {percent:.1f}%</li>")
            return '<ul style="margin-bottom:0.5em;">' + ''.join(items) + '</ul>'
        # Sinon, comportement facial normal
        total = sum(avg_dict.values())
        if total == 0:
            return '<i>Aucune donnée</i>'
        items = []
        for emo, avg in sorted(avg_dict.items(), key=lambda x: -x[1]):
            percent = (avg / total * 100) if total > 0 else 0
            emoji = EMOJI.get(emo, '')
            items.append(f"<li>{emoji} <b>{emo.capitalize()}</b> : {avg:.2f} ({percent:.1f}%)</li>")
        return '<ul style="margin-bottom:0.5em;">' + ''.join(items) + '</ul>'
    
    audio_list = format_emotions_avg_list(audio_emotions_avg, is_audio=True)
    face_list = format_emotions_avg_list(face_emotions_avg)
    
    # Calcul de la moyenne générale positive
    positive_audio = 0
    for k in ['happy', 'calm', 'pleasure']:
        if k in audio_emotions_scores:
            positive_audio += audio_emotions_scores[k]
    total_audio = sum(audio_emotions_scores.values())
    percent_audio = (positive_audio / total_audio * 100) if total_audio > 0 else None
    
    positive_face = 0
    for k in ['happy', 'calm', 'pleasure']:
        if k in face_emotions_scores:
            positive_face += face_emotions_scores[k]
    total_face = sum(face_emotions_scores.values())
    percent_face = (positive_face / total_face * 100) if total_face > 0 else None
    
    percent_text = None
    if text_scores and 'positive' in text_scores:
        percent_text = text_scores['positive']
    
    # Calcul de la moyenne générale
    percent_list = [p for p in [percent_audio, percent_face, percent_text] if p is not None]
    moyenne = sum(percent_list) / len(percent_list) if percent_list else None
    
    # Décision
    main_sentiment = None
    if text_scores:
        sorted_scores = sorted(text_scores.items(), key=lambda x: -x[1])
        main_sentiment = sorted_scores[0][0]
    
    if main_sentiment == 'positive':
        decision = '✅ Passé'
        decision_html = f"<div style='font-size:1.3em;margin-bottom:0.7em;'><b>Décision :</b> <span style='font-size:1.4em'>{decision}</span> <span style='font-size:1em;color:#888;'>(sentiment textuel positif)</span></div>"
    elif moyenne is not None:
        decision = '✅ Passé' if moyenne >= 1 else '❌ Refusé'
        decision_html = f"<div style='font-size:1.3em;margin-bottom:0.7em;'><b>Décision :</b> <span style='font-size:1.4em'>{decision}</span> <span style='font-size:1em;color:#888;'>(moyenne positive : {moyenne:.1f}%)</span></div>"
    else:
        decision_html = "<div style='font-size:1.1em;color:#888;margin-bottom:0.7em;'>Décision automatique impossible (données insuffisantes).</div>"
    
    # Résumé
    audio_main = max(audio_emotions, key=audio_emotions.get) if audio_emotions else 'Aucune'
    face_main = max(face_emotions, key=face_emotions.get) if face_emotions else 'Aucune'
    resume = f"<b>Émotion audio dominante :</b> {EMOJI.get(audio_main, '')} {audio_main}. <b>Émotion faciale dominante :</b> {EMOJI.get(face_main, '')} {face_main}."
    
    # Générer les graphiques
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(1, 2, figsize=(10, 5))
    if audio_emotions:
        axs[0].pie(audio_emotions.values(), labels=audio_emotions.keys(), autopct='%1.1f%%')
        axs[0].set_title('Émotions audio')
    else:
        axs[0].text(0.5, 0.5, 'Aucune donnée audio', ha='center', va='center')
        axs[0].set_title('Émotions audio')
    if face_emotions:
        axs[1].pie(face_emotions.values(), labels=face_emotions.keys(), autopct='%1.1f%%')
        axs[1].set_title('Émotions faciales')
    else:
        axs[1].text(0.5, 0.5, 'Aucune donnée faciale', ha='center', va='center')
        axs[1].set_title('Émotions faciales')
    plt.tight_layout()
    plt.savefig('rapport_emotions.png')
    plt.close(fig)
    
    return render_template(
        'rapport.html',
        slot_id=slot_id,
        decision_html=decision_html,
        resume=resume,
        audio_list=audio_list,
        face_list=face_list,
        transcription=transcription,
        text_scores=text_scores,
        audio_emotions_scores=audio_emotions_scores,
        face_emotions_scores=face_emotions_scores,
        EMOJI=EMOJI,

        debug_info=debug_info
    )

@app.route('/download_pdf_popup', methods=['POST'])
def download_pdf_popup():
    data = request.get_json()
    transcription = data.get('transcription', '')
    text_scores = data.get('text_scores', {})
    slot_id = data.get('slot_id', None)

    # Génère un PDF factice pour le test
    fake_pdf = io.BytesIO(b'%PDF-1.4\n%Fake PDF pour test\n')
    response = make_response(send_file(
        fake_pdf,
        mimetype='application/pdf',
        as_attachment=True,
        download_name='rapport_entretien.pdf'
    ))
    return response