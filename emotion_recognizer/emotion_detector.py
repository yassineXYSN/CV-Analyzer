"""
Enhanced Emotion Detection System for Interview Analysis
Maps standard emotions to interview-relevant categories and adds comprehensive reporting.
"""
import cv2
import numpy as np
import tensorflow as tf
from tensorflow import keras
import os
import json
from datetime import datetime, timedelta
import threading
import time

class EmotionDetector:
    def __init__(self, model_path=None):
        """Initialize the emotion detector with a real trained model"""
        
        # Emotion labels for FER2013 dataset
        self.emotion_labels = ['Angry', 'Disgust', 'Fear', 'Happy', 'Sad', 'Surprise', 'Neutral']
        
        self.interview_emotion_mapping = {
            'Angry': 'anxious',
            'Disgust': 'confused', 
            'Fear': 'anxious',
            'Happy': 'confident',
            'Sad': 'anxious',
            'Surprise': 'confused',
            'Neutral': 'neutral'
        }
        
        # Initialize face detection
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Load the trained model
        self.model = self.load_model(model_path)
        
        # Session data
        self.session_data = {
            'emotions': [],
            'timestamps': [],
            'session_active': False,
            'session_id': None,
            'candidate_name': '',
            'interviewer_name': '',
            'start_time': None,
            'end_time': None
        }
        
        # Real-time stats
        self.current_emotion = 'Neutral'
        self.emotion_confidence = 0.0
        self.emotion_history = []
        
        self.interview_emotions = []  # Track mapped emotions
        
    def load_model(self, model_path=None):
        """Load the pre-trained emotion detection model"""
        if model_path is None:
            # Look for downloaded models
            models_dir = 'models'
            if os.path.exists(models_dir):
                model_files = [f for f in os.listdir(models_dir) if f.endswith('.hdf5')]
                if model_files:
                    model_path = os.path.join(models_dir, model_files[0])
                    print(f"Found model: {model_path}")
                else:
                    print("No .hdf5 model files found in models/ directory")
                    return None
            else:
                print("Models directory not found. Please run download_model.py first")
                return None
        
        try:
            # Load the pre-trained model
            model = keras.models.load_model(model_path)
            print(f"✅ Successfully loaded model: {model_path}")
            print(f"Model input shape: {model.input_shape}")
            print(f"Model output shape: {model.output_shape}")
            return model
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            return None
    
    def preprocess_face(self, face_img):
        """Preprocess face image for model prediction"""
        try:
            # Resize to model input size (typically 48x48 for FER2013 models)
            if self.model is not None:
                target_size = self.model.input_shape[1:3]  # Get height, width from model
            else:
                target_size = (48, 48)  # Default FER2013 size
            
            # Resize and normalize
            face_resized = cv2.resize(face_img, target_size)
            
            # Convert to grayscale if needed
            if len(face_resized.shape) == 3:
                face_gray = cv2.cvtColor(face_resized, cv2.COLOR_BGR2GRAY)
            else:
                face_gray = face_resized
            
            # Normalize pixel values
            face_normalized = face_gray.astype('float32') / 255.0
            
            # Expand dimensions to match model input
            if len(self.model.input_shape) == 4:  # (batch, height, width, channels)
                face_input = np.expand_dims(face_normalized, axis=-1)  # Add channel dimension
                face_input = np.expand_dims(face_input, axis=0)  # Add batch dimension
            else:
                face_input = np.expand_dims(face_normalized, axis=0)  # Add batch dimension
            
            return face_input
        except Exception as e:
            print(f"Error preprocessing face: {e}")
            return None
    
    def predict_emotion(self, face_img):
        """Predict emotion from face image using the trained model"""
        if self.model is None:
            print("⚠️ No model loaded, cannot predict emotions")
            return 'Neutral', 0.0
        
        try:
            # Preprocess the face
            face_input = self.preprocess_face(face_img)
            if face_input is None:
                return 'Neutral', 0.0
            
            # Make prediction using the REAL model (not random!)
            predictions = self.model.predict(face_input, verbose=0)
            
            # Get the emotion with highest probability
            emotion_idx = np.argmax(predictions[0])
            confidence = float(predictions[0][emotion_idx])
            emotion = self.emotion_labels[emotion_idx]
            
            print(f"[v0] Real prediction: {emotion} ({confidence:.2f})")
            return emotion, confidence
            
        except Exception as e:
            print(f"Error predicting emotion: {e}")
            return 'Neutral', 0.0
    
    def detect_faces_and_emotions(self, frame):
        """Detect faces and predict emotions in a frame"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = self.face_cascade.detectMultiScale(
            gray, 
            scaleFactor=1.1, 
            minNeighbors=5, 
            minSize=(30, 30)
        )
        
        results = []
        
        for (x, y, w, h) in faces:
            # Extract face region
            face_roi = frame[y:y+h, x:x+w]
            
            # Predict emotion
            emotion, confidence = self.predict_emotion(face_roi)
            
            # Only accept predictions with reasonable confidence
            if confidence > 0.3:  # Threshold to filter out low-confidence predictions
                results.append({
                    'bbox': (x, y, w, h),
                    'emotion': emotion,
                    'confidence': confidence
                })
                
                # Update current emotion if this is the most confident detection
                if confidence > self.emotion_confidence:
                    self.current_emotion = emotion
                    self.emotion_confidence = confidence
        
        return results
    
    def start_session(self, candidate_name, interviewer_name):
        """Start a new emotion detection session"""
        self.session_data = {
            'emotions': [],
            'timestamps': [],
            'session_active': True,
            'session_id': f"session_{int(time.time())}",
            'candidate_name': candidate_name,
            'interviewer_name': interviewer_name,
            'start_time': datetime.now()
        }
        
        self.emotion_history = []
        self.interview_emotions = []
        
        print(f"✅ Started session: {self.session_data['session_id']}")
        return self.session_data['session_id']
    
    def record_emotion(self, emotion, confidence):
        """Record emotion data during session"""
        if self.session_data['session_active']:
            interview_emotion = self.interview_emotion_mapping.get(emotion, 'neutral')
            
            self.session_data['emotions'].append({
                'emotion': emotion,
                'interview_emotion': interview_emotion,
                'confidence': confidence,
                'timestamp': datetime.now().isoformat()
            })
            
            # Keep emotion history for live stats
            self.emotion_history.append(emotion)
            self.interview_emotions.append(interview_emotion)
            
            if len(self.emotion_history) > 100:  # Keep last 100 emotions
                self.emotion_history.pop(0)
                self.interview_emotions.pop(0)
    
    def get_live_stats(self):
        """Get current emotion statistics mapped to interview categories"""
        if not self.interview_emotions:
            return {
                'current_emotion': 'Neutral',
                'confidence': 0.0,
                'emotion_distribution': {
                    'Anxious': 0,
                    'Confused': 0, 
                    'Confident': 0,
                    'Neutral': 0
                },
                'total_detections': 0,
                'session_duration': 0
            }
        
        emotion_counts = {'anxious': 0, 'confused': 0, 'confident': 0, 'neutral': 0}
        for emotion in self.interview_emotions:
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        
        # Convert to percentages
        total = len(self.interview_emotions)
        emotion_distribution = {
            'Anxious': (emotion_counts['anxious'] / total) * 100,
            'Confused': (emotion_counts['confused'] / total) * 100,
            'Confident': (emotion_counts['confident'] / total) * 100,
            'Neutral': (emotion_counts['neutral'] / total) * 100
        }
        
        session_duration = 0
        if self.session_data['session_active'] and self.session_data['start_time']:
            session_duration = (datetime.now() - self.session_data['start_time']).total_seconds()
        
        current_interview_emotion = self.interview_emotion_mapping.get(self.current_emotion, 'neutral')
        
        return {
            'current_emotion': current_interview_emotion.title(),
            'confidence': self.emotion_confidence,
            'emotion_distribution': emotion_distribution,
            'total_detections': total,
            'session_duration': session_duration
        }
    
    def end_session(self):
        """End the current session and generate report"""
        if not self.session_data['session_active']:
            return None
        
        self.session_data['session_active'] = False
        self.session_data['end_time'] = datetime.now()
        
        # Generate comprehensive report
        report = self.generate_report()
        
        # Save session data
        filename = f"session_report_{self.session_data['session_id']}.json"
        with open(filename, 'w') as f: json.dump({
        'session_data': self.session_data,
        'report': report
    }, f, indent=2, default=str)

        
        print(f"✅ Session ended. Report saved: {filename}")
        return report
    
    def generate_report(self):
        """Generate detailed emotion analysis report with pass/fail logic based on neutral >= 50%"""
        emotions = [e['interview_emotion'] for e in self.session_data['emotions']]
        
        if not emotions:
            return {'message': 'No emotion data recorded', 'interview_result': 'INCOMPLETE'}
        
        emotion_counts = {'anxious': 0, 'confused': 0, 'confident': 0, 'neutral': 0}
        for emotion in emotions:
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        
        total_detections = len(emotions)
        emotion_percentages = {
            emotion: (count / total_detections) * 100 
            for emotion, count in emotion_counts.items()
        }
        
        duration_timedelta = timedelta(seconds=0)
        if self.session_data['start_time'] and self.session_data['end_time']:
            duration_timedelta = self.session_data['end_time'] - self.session_data['start_time']
        
        duration_seconds = duration_timedelta.total_seconds()
        
        # Calculate average confidence
        avg_confidence = np.mean([e['confidence'] for e in self.session_data['emotions']])
        
        confident_percentage = emotion_percentages.get('confident', 0)
        neutral_percentage = emotion_percentages.get('neutral', 0)
        anxious_percentage = emotion_percentages.get('anxious', 0)
        confused_percentage = emotion_percentages.get('confused', 0)
        
        interview_passed = (
            neutral_percentage >= 50.0 and 
            avg_confidence >= 0.4 and 
            duration_seconds >= 30
        )
        
        # Calculate success rate (neutral percentage)
        success_rate = neutral_percentage
        
        # Generate insights
        insights = []
        if neutral_percentage >= 50:
            insights.append("✅ Candidate maintained excellent composure with high neutral emotions")
        if confident_percentage > 30:
            insights.append("✅ Candidate showed good confidence levels")
        if neutral_percentage < 50:
            insights.append("⚠️ Candidate showed insufficient emotional stability (neutral < 50%)")
        if anxious_percentage > 30:
            insights.append("⚠️ Candidate showed signs of anxiety during the interview")
        if confused_percentage > 25:
            insights.append("⚠️ Candidate appeared confused at times")
        if avg_confidence < 0.4:
            insights.append("⚠️ Low detection confidence - results may be unreliable")
        if duration_seconds < 30:
            insights.append("⚠️ Interview session was very short")
        
        # Overall assessment
        if interview_passed:
            overall_assessment = f"PASS - Candidate achieved {neutral_percentage:.1f}% neutral emotions (≥50% required)"
        else:
            reasons = []
            if neutral_percentage < 50:
                reasons.append(f"neutral emotions only {neutral_percentage:.1f}% (need ≥50%)")
            if avg_confidence < 0.4:
                reasons.append("low detection confidence")
            if duration_seconds < 30:
                reasons.append("session too short")
            overall_assessment = f"FAIL - {', '.join(reasons)}"
        
        return {
            'session_id': self.session_data['session_id'],
            'candidate_name': self.session_data['candidate_name'],
            'interviewer_name': self.session_data['interviewer_name'],
            'session_duration': duration_seconds,
            'session_duration_formatted': f"{int(duration_seconds // 60)}:{int(duration_seconds % 60):02d}",
            'total_detections': total_detections,
            'average_confidence': float(avg_confidence),
            'dominant_emotion': max(emotion_counts, key=emotion_counts.get),
            'success_rate': round(success_rate, 2),  # Added success rate field
            'key_metrics': {
                'anxiety_level': round(anxious_percentage, 1),
                'confusion_level': round(confused_percentage, 1),
                'confidence_level': round(confident_percentage, 1),
                'neutral_level': round(neutral_percentage, 1),
            },
            'emotion_distribution': emotion_percentages,
            'interview_result': 'PASS' if interview_passed else 'FAIL',
            'overall_assessment': overall_assessment,
            'insights': insights,
            'recommendations': self._generate_recommendations(emotion_percentages, avg_confidence),
            'session_start_time': self.session_data['start_time'].strftime('%Y-%m-%d %H:%M:%S') if self.session_data['start_time'] else None,
            'session_end_time': self.session_data['end_time'].strftime('%Y-%m-%d %H:%M:%S') if self.session_data['end_time'] else None
        }
    
    def _generate_recommendations(self, emotion_percentages, avg_confidence):
        """Generate recommendations based on emotion analysis"""
        recommendations = []
        
        neutral_pct = emotion_percentages.get('neutral', 0)
        anxious_pct = emotion_percentages.get('anxious', 0)
        confused_pct = emotion_percentages.get('confused', 0)
        confident_pct = emotion_percentages.get('confident', 0)
        
        if neutral_pct < 50:
            recommendations.append("Focus on relaxation techniques and stress management for future interviews")
        if anxious_pct > 30:
            recommendations.append("Consider practicing mindfulness and breathing exercises")
        if confused_pct > 25:
            recommendations.append("Review technical concepts and practice explaining complex topics clearly")
        if confident_pct < 20:
            recommendations.append("Work on building confidence through mock interviews and preparation")
        if avg_confidence < 0.4:
            recommendations.append("Ensure good lighting and camera positioning for better analysis")
        
        if neutral_pct >= 50 and not recommendations:
            recommendations.append("Excellent emotional control! Continue with current interview preparation approach")
        
        return recommendations

# Test the emotion detector
if __name__ == "__main__":
    print("🧪 Testing Emotion Detector with Real Model")
    
    detector = EmotionDetector()
    
    if detector.model is None:
        print("❌ No model loaded. Please run download_model.py first!")
        exit(1)
    
    print("✅ Model loaded successfully!")
    print("Starting camera test...")
    
    cap = cv2.VideoCapture(0)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Detect emotions
        results = detector.detect_faces_and_emotions(frame)
        
        # Draw results
        for result in results:
            x, y, w, h = result['bbox']
            emotion = result['emotion']
            confidence = result['confidence']
            
            # Draw bounding box
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            
            # Draw emotion label
            label = f"{emotion}: {confidence:.2f}"
            cv2.putText(frame, label, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
        
        cv2.imshow('Emotion Detection', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
