from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from fastapi.responses import RedirectResponse
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from databasehr.database import SessionLocal
from databasehr.models import Application
import os
import json
import tempfile
import whisper
import cv2
from deepface import DeepFace
from datetime import datetime, timedelta
import requests

router = APIRouter(prefix="/api/hr", tags=["ai-interview-analysis"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class ConversationEmotionAnalyzer:
    def __init__(self, whisper_model_size: str = "base"):
        """Initialize the analyzer with Whisper and DeepFace models"""
        print("Initializing AI models...")
        self.whisper_model = whisper.load_model(whisper_model_size)
        print("Models loaded successfully!")
    
    def transcribe_audio(self, audio_path: str, speaker_name: str = "Speaker") -> List[Dict]:
        """Transcribe audio file and return segments with timestamps"""
        print(f"Transcribing {speaker_name}'s audio...")
        
        result = self.whisper_model.transcribe(
            audio_path,
            word_timestamps=False,
            task="translate"  # Forces translation to English
        )
        
        segments = []
        for segment in result["segments"]:
            segments.append({
                "speaker": speaker_name,
                "text": segment["text"].strip(),
                "start": segment["start"],
                "end": segment["end"],
                "language": "english"
            })
        
        print(f"Transcribed {len(segments)} segments for {speaker_name}")
        return segments
    
    def analyze_video_emotions(self, video_path: str, frame_interval: int = 30) -> List[Dict]:
        """Analyze emotions in video and return results with timestamps"""
        print("Starting video emotion analysis...")
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError("Error: Could not open video file")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        print(f"Video FPS: {fps}, Total frames: {total_frames}")
        
        results = []
        frame_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            if frame_count % frame_interval == 0:
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                try:
                    analysis = DeepFace.analyze(rgb_frame, actions=['emotion'], enforce_detection=False)
                    timestamp = frame_count / fps
                    time_str = str(datetime.utcfromtimestamp(timestamp).strftime('%H:%M:%S.%f')[:-3])
                    
                    emotions = analysis[0]['emotion']
                    dominant_emotion = max(emotions.items(), key=lambda x: x[1])
                    
                    result = {
                        'frame': frame_count,
                        'timestamp': timestamp,
                        'timestamp_formatted': time_str,
                        'dominant_emotion': dominant_emotion[0],
                        'emotion_confidence': dominant_emotion[1],
                        'all_emotions': emotions
                    }
                    
                    results.append(result)
                    
                except Exception as e:
                    print(f"Error processing frame {frame_count}: {str(e)}")
                    timestamp = frame_count / fps
                    time_str = str(datetime.utcfromtimestamp(timestamp).strftime('%H:%M:%S.%f')[:-3])
                    
                    results.append({
                        'frame': frame_count,
                        'timestamp': timestamp,
                        'timestamp_formatted': time_str,
                        'dominant_emotion': 'unknown',
                        'emotion_confidence': 0,
                        'all_emotions': {}
                    })
            
            frame_count += 1
        
        cap.release()
        print(f"Video emotion analysis complete! Processed {len(results)} frames")
        return results
    
    def merge_conversation(self, segments1: List[Dict], segments2: List[Dict]) -> List[Dict]:
        """Merge segments from two speakers by timestamp"""
        all_segments = segments1 + segments2
        all_segments.sort(key=lambda x: x["start"])
        return all_segments
    
    def assign_emotions_to_conversation(self, conversation: List[Dict], emotion_data: List[Dict]) -> List[Dict]:
        """Assign emotion data to conversation segments based on timestamps"""
        print("Assigning emotions to conversation segments...")
        
        for segment in conversation:
            segment_start = segment["start"]
            segment_end = segment["end"]
            
            segment_emotions = []
            for emotion in emotion_data:
                if segment_start <= emotion["timestamp"] <= segment_end:
                    segment_emotions.append(emotion)
            
            if segment_emotions:
                emotion_counts = {}
                emotion_confidences = {}
                
                for emo in segment_emotions:
                    emotion = emo["dominant_emotion"]
                    if emotion != "unknown":
                        emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
                        emotion_confidences[emotion] = emotion_confidences.get(emotion, 0) + emo["emotion_confidence"]
                
                if emotion_counts:
                    dominant_emotion = max(emotion_counts.items(), key=lambda x: x[1])
                    avg_confidence = emotion_confidences[dominant_emotion[0]] / emotion_counts[dominant_emotion[0]]
                    
                    segment["emotion"] = dominant_emotion[0]
                    segment["emotion_confidence"] = avg_confidence
                    segment["emotion_samples"] = len(segment_emotions)
                else:
                    segment["emotion"] = "unknown"
                    segment["emotion_confidence"] = 0
                    segment["emotion_samples"] = 0
            else:
                segment["emotion"] = "unknown"
                segment["emotion_confidence"] = 0
                segment["emotion_samples"] = 0
        
        return conversation
    
    def format_conversation(self, merged_segments: List[Dict], min_gap: float = 2.0) -> List[Dict]:
        """Format the conversation with proper grouping and timing"""
        if not merged_segments:
            return []
        
        formatted = []
        current_speaker = merged_segments[0]["speaker"]
        current_text = merged_segments[0]["text"]
        current_start = merged_segments[0]["start"]
        current_end = merged_segments[0]["end"]
        current_emotions = [merged_segments[0].get("emotion", "unknown")]
        
        for i in range(1, len(merged_segments)):
            segment = merged_segments[i]
            
            if (segment["speaker"] == current_speaker and 
                segment["start"] - current_end < min_gap):
                current_text += " " + segment["text"]
                current_end = segment["end"]
                current_emotions.append(segment.get("emotion", "unknown"))
            else:
                if current_emotions:
                    emotion_counts = {}
                    for emotion in current_emotions:
                        if emotion != "unknown":
                            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
                    
                    dominant_emotion = max(emotion_counts.items(), key=lambda x: x[1])[0] if emotion_counts else "unknown"
                else:
                    dominant_emotion = "unknown"
                
                formatted.append({
                    "speaker": current_speaker,
                    "text": current_text,
                    "start": current_start,
                    "end": current_end,
                    "duration": current_end - current_start,
                    "emotion": dominant_emotion,
                    "emotion_samples": len(current_emotions)
                })
                
                current_speaker = segment["speaker"]
                current_text = segment["text"]
                current_start = segment["start"]
                current_end = segment["end"]
                current_emotions = [segment.get("emotion", "unknown")]
        
        if current_emotions:
            emotion_counts = {}
            for emotion in current_emotions:
                if emotion != "unknown":
                    emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
            
            dominant_emotion = max(emotion_counts.items(), key=lambda x: x[1])[0] if emotion_counts else "unknown"
        else:
            dominant_emotion = "unknown"
        
        formatted.append({
            "speaker": current_speaker,
            "text": current_text,
            "start": current_start,
            "end": current_end,
            "duration": current_end - current_start,
            "emotion": dominant_emotion,
            "emotion_samples": len(current_emotions)
        })
        
        return formatted

@router.post("/ai-interview-analysis")
async def analyze_interview_with_ai(
    candidate_id: int = Form(...),
    hr_audio: Optional[UploadFile] = File(None),
    candidate_audio: Optional[UploadFile] = File(None),
    interview_video: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """
    Endpoint pour l'analyse IA des fichiers média d'entretien.
    """
    try:
        # Vérifier que l'application existe
        application = db.query(Application).filter(
            Application.candidate_profile_id == candidate_id
        ).first()
        
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        
        # Vérifier qu'au moins un fichier est fourni
        if not hr_audio and not candidate_audio and not interview_video:
            raise HTTPException(status_code=400, detail="At least one media file is required")
        
        # Créer des fichiers temporaires
        temp_files = []
        analyzer = ConversationEmotionAnalyzer()
        
        try:
            # Sauvegarder les fichiers uploadés
            hr_audio_path = None
            candidate_audio_path = None
            video_path = None
            
            if hr_audio:
                hr_audio_path = tempfile.mktemp(suffix=".wav")
                with open(hr_audio_path, "wb") as f:
                    f.write(await hr_audio.read())
                temp_files.append(hr_audio_path)
            
            if candidate_audio:
                candidate_audio_path = tempfile.mktemp(suffix=".wav")
                with open(candidate_audio_path, "wb") as f:
                    f.write(await candidate_audio.read())
                temp_files.append(candidate_audio_path)
            
            if interview_video:
                video_path = tempfile.mktemp(suffix=".mp4")
                with open(video_path, "wb") as f:
                    f.write(await interview_video.read())
                temp_files.append(video_path)
            
            # Analyser les fichiers
            segments1 = []
            segments2 = []
            emotion_data = []
            
            if hr_audio_path:
                segments1 = analyzer.transcribe_audio(hr_audio_path, "Interviewer")
            
            if candidate_audio_path:
                segments2 = analyzer.transcribe_audio(candidate_audio_path, "Interviewee")
            
            if video_path:
                emotion_data = analyzer.analyze_video_emotions(video_path)
            
            # Fusionner et analyser la conversation
            if segments1 or segments2:
                merged_conversation = analyzer.merge_conversation(segments1, segments2)
                conversation_with_emotions = analyzer.assign_emotions_to_conversation(merged_conversation, emotion_data)
                final_conversation = analyzer.format_conversation(conversation_with_emotions)
                
                # Convertir en format de réponse
                analysis_result = []
                for turn in final_conversation:
                    analysis_result.append({
                        "speaker": turn["speaker"],
                        "emotion": turn["emotion"],
                        "text": turn["text"]
                    })
                
                # Sauvegarder dans la base de données
                application.ai_interview_analysis = json.dumps(analysis_result)
                db.commit()
                
                # Return success response instead of redirect
                return {
                    "success": True,
                    "message": "Analyse IA terminée avec succès",
                    "candidate_id": candidate_id,
                    "analysis": analysis_result,
                    "files_processed": {
                        "hr_audio": hr_audio is not None,
                        "candidate_audio": candidate_audio is not None,
                        "interview_video": interview_video is not None
                    }
                }
            else:
                raise HTTPException(status_code=400, detail="No valid audio files found for transcription")
        
        finally:
            # Nettoyer les fichiers temporaires
            for temp_file in temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                except Exception as e:
                    print(f"Error removing temp file {temp_file}: {e}")
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'analyse IA: {str(e)}")

@router.get("/ai-interview-analysis/{candidate_id}")
async def get_interview_analysis(candidate_id: int, db: Session = Depends(get_db)):
    """Récupérer l'analyse IA d'un candidat"""
    try:
        application = db.query(Application).filter(
            Application.candidate_profile_id == candidate_id
        ).first()
        
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        
        if not application.ai_interview_analysis:
            raise HTTPException(status_code=404, detail="No AI analysis found for this candidate")
        
        analysis = json.loads(application.ai_interview_analysis)
        
        return {
            "success": True,
            "candidate_id": candidate_id,
            "analysis": analysis
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération de l'analyse: {str(e)}")
