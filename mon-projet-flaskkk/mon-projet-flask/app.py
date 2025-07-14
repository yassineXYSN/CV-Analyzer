import os
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import logging
from flask_mail import Mail, Message
import uuid
import requests
import time
from pytz import timezone
from flask_socketio import SocketIO, emit
import speech_recognition as sr
import threading
from transformers import pipeline
import torchaudio
import whisper

# Configurer le logging pour débogage
logging.basicConfig(
    level=logging.INFO,
    filename='app.log',
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s'
)

app = Flask(__name__)

ASSEMBLYAI_API_KEY = "962e317e6e204907ac73857fafa4cdce"
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Configuration base de données MySQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/mon_projet_flask'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configuration Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'nour.hasni02@gmail.com'
app.config['MAIL_PASSWORD'] = 'ithyrphenumuusug'  # Utiliser mot de passe d'application
app.config['SECRET_KEY'] = 'a0316815ed2f6a7ffc92305a7e95699f82f86183c09ba037'

# Initialisation extensions
mail = Mail(app)
db = SQLAlchemy(app)
socketio = SocketIO(app, async_mode='threading')

# Reconnaissance vocale
recognizer = sr.Recognizer()

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
    is_booked = db.Column(db.Boolean, default=False, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending', nullable=False)
    meet_link = db.Column(db.String(255))
    transcription = db.Column(db.Text)
    emotions_data = db.Column(db.Text)  # Stockage des émotions en JSON

    def __repr__(self):
        return f'<TimeSlot {self.start_time} - {self.end_time}, Status: {self.status}>'

class Transcript(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    transcript_id = db.Column(db.String(100), unique=True, nullable=False)
    text = db.Column(db.Text)
    emotions = db.Column(db.Text)  # ou JSON si tu préfères, selon ta base

    def __repr__(self):
        return f'<Transcript {self.transcript_id}>'

def save_transcript_to_db(transcript_id, text, emotions):
    transcript = Transcript.query.filter_by(transcript_id=transcript_id).first()
    if transcript:
        transcript.text = text
        transcript.emotions = emotions
    else:
        transcript = Transcript(
            transcript_id=transcript_id,
            text=text,
            emotions=emotions  # selon le type de champ (JSON, string, etc)
        )
        db.session.add(transcript)
    db.session.commit()

# Fonction pour analyser les émotions d'un texte
def analyze_emotions(text):
    """Analyse les émotions d'un texte en utilisant des mots-clés"""
    emotions = {
        'joy': ['heureux', 'content', 'joyeux', 'excellent', 'super', 'génial', 'fantastique', 'merveilleux'],
        'sadness': ['triste', 'déprimé', 'malheureux', 'désolé', 'déçu', 'découragé'],
        'anger': ['fâché', 'en colère', 'furieux', 'irrité', 'énervé', 'exaspéré'],
        'fear': ['peur', 'effrayé', 'inquiet', 'anxieux', 'stressé', 'paniqué'],
        'surprise': ['surpris', 'étonné', 'stupéfait', 'incroyable', 'wow'],
        'neutral': ['normal', 'ok', 'bien', 'correct', 'standard']
    }
    
    text_lower = text.lower()
    detected_emotions = []
    
    for emotion, keywords in emotions.items():
        for keyword in keywords:
            if keyword in text_lower:
                detected_emotions.append(emotion)
                break
    
    if not detected_emotions:
        detected_emotions = ['neutral']
    
    return detected_emotions

# Lazy loader pour le pipeline d'émotion
emotion_pipe = None

def get_emotion_pipe():
    global emotion_pipe
    if emotion_pipe is None:
        try:
            emotion_pipe = pipeline(
                task="audio-classification",
                model="ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition"  # Multilingue : anglais, français, arabe
            )
            logging.info("Pipeline d'émotion audio chargé avec succès (multilingue)")
        except Exception as e:
            logging.error(f"Erreur lors du chargement du pipeline d'émotion: {e}")
            emotion_pipe = None
    return emotion_pipe

# Charger le modèle Whisper une seule fois
whisper_model = None
def get_whisper_model():
    global whisper_model
    if whisper_model is None:
        whisper_model = whisper.load_model("base")  # ou "small" pour plus rapide
    return whisper_model

# Fonction de transcription audio avec détection d'émotions en temps réel
def transcribe_audio_with_emotions(slot_id):
    with app.app_context():
        slot = TimeSlot.query.get(slot_id)
        if not slot:
            logging.error(f"Créneau {slot_id} non trouvé")
            return
        
        try:
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=1)
                logging.info(f"Transcription démarrée pour le slot {slot_id}")
                
                while True:
                    try:
                        audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
                        text = recognizer.recognize_google(audio, language='fr-FR')
                        
                        if text.strip():
                            # Analyser les émotions
                            emotions = analyze_emotions(text)
                            
                            # Mettre à jour la transcription
                            slot.transcription = (slot.transcription or '') + text + '\n'
                            
                            # Stocker les émotions
                            import json
                            emotions_data = {
                                'text': text,
                                'emotions': emotions,
                                'timestamp': datetime.now().isoformat()
                            }
                            
                            if slot.emotions_data:
                                existing_emotions = json.loads(slot.emotions_data)
                                existing_emotions.append(emotions_data)
                                slot.emotions_data = json.dumps(existing_emotions)
                            else:
                                slot.emotions_data = json.dumps([emotions_data])
                            
                            db.session.commit()
                            
                            # Envoyer les données via SocketIO
                            socketio.emit('transcription_update', {
                                'slot_id': slot_id, 
                                'text': text,
                                'emotions': emotions,
                                'full_transcription': slot.transcription
                            })
                            
                            logging.info(f"Transcription: {text} | Émotions: {emotions}")
                            
                    except sr.WaitTimeoutError:
                        continue
                    except sr.UnknownValueError:
                        logging.warning("Audio non compris")
                    except sr.RequestError as e:
                        logging.error(f"Erreur de service de transcription: {e}")
                        socketio.emit('transcription_error', {
                            'slot_id': slot_id,
                            'error': str(e)
                        })
                        break
                        
        except Exception as e:
            logging.error(f"Erreur dans la fonction transcribe_audio_with_emotions: {str(e)}")
            socketio.emit('transcription_error', {
                'slot_id': slot_id,
                'error': str(e)
            })

# Fonction de transcription audio (microphone local) - version simplifiée
def transcribe_audio(slot_id):
    with app.app_context():
        slot = TimeSlot.query.get(slot_id)
        if not slot:
            logging.error(f"Créneau {slot_id} non trouvé")
            return
        try:
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
        except Exception as e:
            logging.error(f"Erreur dans la fonction transcribe_audio: {str(e)}")

def detect_audio_emotion(audio_path):
    try:
        pipe = get_emotion_pipe()
        if pipe is None:
            logging.warning("Pipeline d'émotion non disponible")
            return "neutral"
        
        # Charger l'audio et le convertir en 16kHz mono
        waveform, sample_rate = torchaudio.load(audio_path)
        if sample_rate != 16000:
            waveform = torchaudio.functional.resample(waveform, sample_rate, 16000)
        
        # HuggingFace attend un chemin ou un tableau numpy
        result = pipe(audio_path)
        # Prendre l'émotion la plus probable
        emotion = result[0]['label']
        logging.info(f"Émotion détectée: {emotion}")
        return emotion
    except Exception as e:
        logging.error(f"Erreur détection émotion audio: {e}")
        return "neutral"

def transcribe_and_store_assemblyai(audio_path, audio_id):
    """Lance la transcription AssemblyAI en tâche de fond et stocke le résultat en BDD."""
    try:
        with open(audio_path, 'rb') as f:
            upload_response = requests.post(
                'https://api.assemblyai.com/v2/upload',
                headers={'authorization': ASSEMBLYAI_API_KEY},
                data=f
            )
        if upload_response.status_code != 200:
            logging.error('Erreur upload AssemblyAI')
            return
        upload_url = upload_response.json()['upload_url']
        transcript_request = {
            "audio_url": upload_url,
            "language_code": "fr",
            "sentiment_analysis": True,
            "auto_chapters": False,
            "iab_categories": False,
            "entity_detection": False,
            "content_safety": False,
            "auto_highlights": False,
            "punctuate": True
        }
        transcript_response = requests.post(
            'https://api.assemblyai.com/v2/transcript',
            json=transcript_request,
            headers={'authorization': ASSEMBLYAI_API_KEY}
        )
        if transcript_response.status_code != 200:
            logging.error('Erreur transcription AssemblyAI')
            return
        transcript_id = transcript_response.json()['id']
        # Attendre que la transcription soit prête
        status = 'queued'
        while status not in ['completed', 'failed']:
            r = requests.get(f'https://api.assemblyai.com/v2/transcript/{transcript_id}', headers={'authorization': ASSEMBLYAI_API_KEY})
            data = r.json()
            status = data.get('status')
            if status == 'completed':
                text = data.get('text', '')
                emotions = data.get('sentiment_analysis_results', None)
                # Stocker en BDD
                from mon_projet_flask.app import Transcript, db
                transcript = Transcript.query.filter_by(transcript_id=audio_id).first()
                if not transcript:
                    transcript = Transcript(transcript_id=audio_id, text=text, emotions=emotions)
                    db.session.add(transcript)
                else:
                    transcript.text = text
                    transcript.emotions = emotions
                db.session.commit()
                logging.info(f"Transcription stockée pour {audio_id}")
                break
            elif status == 'failed':
                logging.error(f"Transcription AssemblyAI échouée pour {audio_id}")
                break
            time.sleep(3)
    except Exception as e:
        logging.error(f"Erreur transcription AssemblyAI: {e}")

@app.route('/realtime-transcribe', methods=['POST'])
def realtime_transcribe():
    data = request.json
    text = data.get('text', '')
    slot_id = data.get('slot_id')
    
    if text.strip():
        # Analyser les émotions
        emotions = analyze_emotions(text)
        
        # Envoyer via SocketIO
        socketio.emit('realtime_transcription', {
            'text': text,
            'emotions': emotions,
            'slot_id': slot_id
        })
        
        logging.info(f"💬 Phrase reçue : {text} | Émotions: {emotions}")
    
    return jsonify({"status": "ok", "message": "Reçu", "text": text, "emotions": emotions if 'emotions' in locals() else []})

@app.route('/start_transcription/<int:slot_id>', methods=['POST'])
def start_transcription(slot_id):
    try:
        # Vérifier si le slot existe
        slot = TimeSlot.query.get(slot_id)
        if not slot:
            return jsonify({'success': False, 'message': 'Créneau non trouvé'}), 404
        
        # Démarrer la transcription avec émotions
        threading.Thread(target=transcribe_audio_with_emotions, args=(slot_id,), daemon=True).start()
        
        logging.info(f"Transcription démarrée pour le slot {slot_id}")
        return jsonify({'success': True, 'message': 'Transcription démarrée'})
        
    except Exception as e:
        logging.error(f"Erreur lors du démarrage de la transcription: {str(e)}")
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'}), 500

@app.route('/upload-audio', methods=['POST'])
def upload_audio():
    if 'audio' not in request.files:
        return jsonify({'error': 'Aucun fichier audio fourni'}), 400

    audio_file = request.files['audio']
    audio_id = uuid.uuid4().hex
    filename = os.path.join(UPLOAD_FOLDER, f"{audio_id}.webm")
    audio_file.save(filename)

    # Détection d'émotion sur l'audio (immédiate)
    emotion = detect_audio_emotion(filename)

    # Transcription locale instantanée avec Whisper
    try:
        model = get_whisper_model()
        result = model.transcribe(filename)  # Laisse Whisper détecter la langue
        text = result['text']
    except Exception as e:
        logging.error(f"Erreur transcription Whisper: {e}")
        text = ""

    # Lancer la transcription AssemblyAI en tâche de fond (optionnel)
    threading.Thread(target=transcribe_and_store_assemblyai, args=(filename, audio_id), daemon=True).start()

    # Réponse immédiate avec l'émotion détectée, la transcription locale et l'id du segment
    return jsonify({'audio_emotion': emotion, 'audio_id': audio_id, 'text': text})

@app.route('/get-transcription/<audio_id>')
def get_transcription(audio_id):
    transcript = Transcript.query.filter_by(transcript_id=audio_id).first()
    if not transcript:
        return jsonify({'status': 'pending', 'message': 'Transcription en cours'}), 202
    return jsonify({
        'status': 'completed',
        'text': transcript.text,
        'emotions': transcript.emotions
    })

# Route pour obtenir la transcription (AssemblyAI)
@app.route('/transcription-result/<transcript_id>')
def get_transcription_result(transcript_id):
    headers = {'authorization': ASSEMBLYAI_API_KEY}
    response = requests.get(f'https://api.assemblyai.com/v2/transcript/{transcript_id}', headers=headers)
    data = response.json()

    if data.get('status') == 'completed':
        # Sauvegarde en BDD
        existing = Transcript.query.filter_by(transcript_id=transcript_id).first()
        if not existing:
            transcript = Transcript(
                transcript_id=transcript_id,
                text=data.get('text', ''),
                emotions=data.get('sentiment_analysis_results', None)  # ou autre champ
            )
            db.session.add(transcript)
            db.session.commit()

    return jsonify(data)

@app.route('/emotions-stats/<int:slot_id>')
def get_emotions_stats(slot_id):
    try:
        slot = TimeSlot.query.get(slot_id)
        if not slot or not slot.emotions_data:
            return jsonify({'emotions': {}})
        
        import json
        emotions_data = json.loads(slot.emotions_data)
        
        # Compter les émotions
        emotion_counts = {}
        for entry in emotions_data:
            for emotion in entry.get('emotions', []):
                emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        
        return jsonify({'emotions': emotion_counts})
        
    except Exception as e:
        logging.error(f"Erreur lors de la récupération des statistiques d'émotions: {str(e)}")
        return jsonify({'error': str(e)}), 500


# Vérification des entretiens à venir
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

# Routes principales
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

        # Envoi email confirmation
        try:
            msg_candidate = Message('Confirmation de votre inscription',
                                   sender=app.config['MAIL_USERNAME'],
                                   recipients=[email])
            msg_candidate.body = f"Bonjour {name},\n\nVotre inscription a été reçue avec succès. Veuillez choisir un créneau pour votre entretien sur la page suivante.\n\nCordialement,\nL'équipe RH"
            mail.send(msg_candidate)
            logging.info(f"E-mail de confirmation envoyé à {email}")
        except Exception as e:
            logging.error(f"Erreur lors de l'envoi de l'e-mail à {email}: {str(e)}", exc_info=True)
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

        user = User.query.get(user_id)
        if not user:
            logging.error(f"Utilisateur {user_id} non trouvé")
            return jsonify({'success': False, 'message': 'Utilisateur non trouvé.'}), 400

        meet_room_name = f"entretien_{new_slot.id}_{uuid.uuid4().hex[:8]}"
        meet_link = url_for('interview', slot_id=new_slot.id, meet_room_name=meet_room_name, user_name=user.name, _external=True)
        new_slot.meet_link = meet_link
        db.session.commit()
        logging.info(f"Lien Jitsi généré pour slot {new_slot.id}: {meet_link}")

        try:
            msg_candidate = Message('Confirmation de votre entretien',
                                   sender=app.config['MAIL_USERNAME'],
                                   recipients=[user.email])
            msg_candidate.body = f"Bonjour {user.name},\n\nVotre entretien est confirmé pour le {start_time}. Cliquez sur ce lien pour rejoindre : {meet_link}\n\nCordialement,\nL'équipe RH"
            mail.send(msg_candidate)
            logging.info(f"E-mail envoyé à {user.email} pour confirmation de l'entretien.")
        except Exception as e:
            logging.error(f"Erreur lors de l'envoi du mail à {user.email}: {str(e)}", exc_info=True)

        try:
            msg_recruiter = Message('Nouvel entretien programmé',
                                   sender=app.config['MAIL_USERNAME'],
                                   recipients=[recruiter_email])
            msg_recruiter.body = f"Bonjour,\n\nUn entretien avec {user.name} est programmé le {start_time}. Lien : {meet_link}\n\nCordialement,\nL'équipe RH"
            mail.send(msg_recruiter)
            logging.info(f"E-mail envoyé à {recruiter_email} pour notification d'entretien.")
        except Exception as e:
            logging.error(f"Erreur lors de l'envoi du mail à {recruiter_email}: {str(e)}", exc_info=True)

        return jsonify({'success': True, 'message': 'Créneau réservé avec succès.'})

    return jsonify({'success': False, 'message': 'Créneau invalide.'}), 400

# -----------------
# --- SocketIO Events
# -----------------

@socketio.on('start_transcription')
def handle_start_transcription(data):
    slot_id = data.get('slot_id')
    if not slot_id:
        emit('error', {'message': 'slot_id manquant'})
        return

    # Lancer un thread de transcription (exemple simple)
    threading.Thread(target=transcribe_audio_with_emotions, args=(slot_id,), daemon=True).start()
    emit('transcription_started', {'slot_id': slot_id})

# -----------------
# --- Scheduler pour les entretiens à venir
# -----------------

def start_scheduler():
    scheduler = BackgroundScheduler(timezone='Africa/Tunis')
    scheduler.add_job(check_upcoming_interviews, 'interval', minutes=1)
    scheduler.start()

@socketio.on('realtime_speech')
def handle_realtime_speech(data):
    text = data.get('text', '')
    print(f"🔊 Texte reçu via WebSocket : {text}")
    emit('realtime_transcription', {'text': text}, broadcast=True)

# -----------------
# --- Point d'entrée principal
# -----------------

# Exécution app avec SocketIO
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

