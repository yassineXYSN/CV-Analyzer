import cv2
from deepface import DeepFace
import pandas as pd
from datetime import datetime
import whisper
import json
import os
from pydub import AudioSegment
import logging
from collections import defaultdict
import numpy as np

# Set up logging
logging.basicConfig(level=logging.WARNING)

def make_json_serializable(obj):
    """Recursively convert numpy types/arrays to native Python types so json can serialize."""
    if isinstance(obj, dict):
        return {make_json_serializable(k): make_json_serializable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [make_json_serializable(v) for v in obj]
    # numpy scalars
    if isinstance(obj, np.generic):
        return obj.item()
    # numpy arrays
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    return obj

class EmotionTranscriptionAnalyzer:
    def __init__(self):
        self.whisper_model = None
        self.emotion_results = []
        self.transcription_results = []
        
    def load_whisper_model(self, model_size="large"):
        """Load the Whisper model for transcription"""
        print("Loading Whisper model...")
        self.whisper_model = whisper.load_model(model_size)
        print("Model loaded successfully!")
        
    def get_audio_duration(self, path):
        """Return duration in seconds using pydub."""
        if not os.path.exists(path):
            raise FileNotFoundError(f"Audio file not found: {path}")
        audio = AudioSegment.from_file(path)
        return len(audio) / 1000.0

    def transcribe_audio_with_timestamps(self, audio_path, speaker_name, language=None, multi_language=False):
        """
        Transcribe audio with timestamps
        
        Args:
            audio_path: Path to audio file
            speaker_name: Name of speaker for labeling
            language: Specific language code (e.g., "en", "fr")
            multi_language: Whether to enable multi-language detection
        """
        if not self.whisper_model:
            self.load_whisper_model()
            
        if multi_language:
            result = self.whisper_model.transcribe(audio_path, language=None, task="transcribe")
        elif language:
            result = self.whisper_model.transcribe(audio_path, language=language)
        else:
            result = self.whisper_model.transcribe(audio_path)
        
        segments = []
        for seg in result["segments"]:
            segment_data = {
                "start": seg["start"],
                "end": seg["end"],
                "text": seg["text"].strip(),
                "speaker": speaker_name
            }
            
            if multi_language and "language" in seg:
                segment_data["detected_language"] = seg["language"]
            elif multi_language:
                segment_data["detected_language"] = result.get("language", "unknown")
            
            segments.append(segment_data)
        
        return segments

    def analyze_video_emotions(self, video_path, frame_interval=30):
        """
        Analyze emotions in a video and return results with timestamps
        
        Args:
            video_path (str): Path to input video file
            frame_interval (int): Analyze every nth frame (higher = faster processing)
        """
        # Open video file
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError("Error: Could not open video file")
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        print(f"Video FPS: {fps}")
        print(f"Total frames: {total_frames}")
        print("Starting emotion analysis...")
        
        results = []
        frame_count = 0
        
        while True:
            ret, frame = cap.read()
            
            if not ret:
                break
                
            # Process frame at specified interval
            if frame_count % frame_interval == 0:
                # Convert BGR to RGB
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                try:
                    # Analyze emotion
                    analysis = DeepFace.analyze(rgb_frame, actions=['emotion'], enforce_detection=False)
                    
                    # Calculate timestamp
                    timestamp = frame_count / fps
                    
                    # Format timestamp
                    time_str = str(datetime.utcfromtimestamp(timestamp).strftime('%H:%M:%S.%f')[:-3])
                    
                    # Get dominant emotion
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
                    
                    print(f"Frame {frame_count} ({time_str}): {dominant_emotion[0]} ({dominant_emotion[1]:.2f}%)")
                    
                except Exception as e:
                    print(f"Error processing frame {frame_count}: {str(e)}")
                    # Add entry even if analysis fails
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
        self.emotion_results = results
        print(f"\nEmotion analysis complete! Processed {len(results)} frames")
        return results

    def assign_emotions_to_transcription(self, transcription_segments, emotion_results):
        """
        Assign emotions to transcription segments based on timestamp matching
        
        Args:
            transcription_segments: List of transcription segments with timestamps
            emotion_results: List of emotion analysis results with timestamps
        """
        enhanced_segments = []
        
        for segment in transcription_segments:
            segment_start = segment['start']
            segment_end = segment['end']
            
            # Find emotions that occurred during this speech segment
            segment_emotions = []
            for emotion in emotion_results:
                if segment_start <= emotion['timestamp'] <= segment_end:
                    segment_emotions.append(emotion)
            
            # Calculate dominant emotion for this segment
            if segment_emotions:
                # Count emotion occurrences
                emotion_count = defaultdict(int)
                emotion_confidences = defaultdict(list)
                
                for emo in segment_emotions:
                    emotion_count[emo['dominant_emotion']] += 1
                    emotion_confidences[emo['dominant_emotion']].append(emo['emotion_confidence'])
                
                # Find most frequent emotion
                if emotion_count:
                    dominant_emotion = max(emotion_count.items(), key=lambda x: x[1])[0]
                    avg_confidence = sum(emotion_confidences[dominant_emotion]) / len(emotion_confidences[dominant_emotion])
                else:
                    dominant_emotion = "unknown"
                    avg_confidence = 0
            else:
                dominant_emotion = "unknown"
                avg_confidence = 0
                segment_emotions = []
            
            # Create enhanced segment with emotion information
            enhanced_segment = segment.copy()
            enhanced_segment.update({
                'assigned_emotion': dominant_emotion,
                'emotion_confidence': avg_confidence,
                'emotion_samples_count': len(segment_emotions),
                'emotion_timestamps': [e['timestamp'] for e in segment_emotions]
            })
            
            enhanced_segments.append(enhanced_segment)
        
        return enhanced_segments

    def analyze_complete_session(self, audio_file1, audio_file2, video_file, 
                               output_prefix="session_analysis", 
                               language=None, multi_language=True,
                               frame_interval=30):
        """
        Complete analysis of two audio files and one video file
        
        Args:
            audio_file1: First audio file path
            audio_file2: Second audio file path  
            video_file: Video file path
            output_prefix: Prefix for output files
            language: Language for transcription
            multi_language: Enable multi-language detection
            frame_interval: Frame interval for emotion analysis
        """
        
        # Check if files exist
        for file_path in [audio_file1, audio_file2, video_file]:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
        
        print("=== STARTING COMPREHENSIVE ANALYSIS ===")
        
        # Step 1: Analyze video emotions
        print("\n1. Analyzing video emotions...")
        emotion_results = self.analyze_video_emotions(video_file, frame_interval)
        
        # Step 2: Transcribe audio files
        print("\n2. Transcribing audio files...")
        
        # Determine speaker names based on duration
        dur1 = self.get_audio_duration(audio_file1)
        dur2 = self.get_audio_duration(audio_file2)
        
        print(f"Audio 1: {os.path.basename(audio_file1)} ({dur1:.2f}s)")
        print(f"Audio 2: {os.path.basename(audio_file2)} ({dur2:.2f}s)")
        
        if dur1 >= dur2:
            speaker1, speaker2 = "Speaker 1", "Speaker 2"
        else:
            speaker1, speaker2 = "Speaker 2", "Speaker 1"
        
        # Transcribe both audio files
        transcription1 = self.transcribe_audio_with_timestamps(
            audio_file1, speaker1, language, multi_language)
        transcription2 = self.transcribe_audio_with_timestamps(
            audio_file2, speaker2, language, multi_language)
        
        # Merge transcriptions
        all_transcriptions = transcription1 + transcription2
        merged_transcriptions = sorted(all_transcriptions, key=lambda x: x["start"])
        
        # Step 3: Assign emotions to transcription segments
        print("\n3. Assigning emotions to transcription segments...")
        enhanced_transcriptions = self.assign_emotions_to_transcription(
            merged_transcriptions, emotion_results)
        
        # Step 4: Generate outputs
        print("\n4. Generating output files...")
        
        # Save enhanced transcriptions with emotions
        output_json = f"{output_prefix}_enhanced.json"
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(make_json_serializable(enhanced_transcriptions), f, ensure_ascii=False, indent=2)
        
        # Save readable text version
        output_txt = f"{output_prefix}_readable.txt"
        with open(output_txt, "w", encoding="utf-8") as f:
            f.write("ENHANCED TRANSCRIPTION WITH EMOTION ANALYSIS\n")
            f.write("=" * 60 + "\n\n")
            
            for segment in enhanced_transcriptions:
                emotion_info = f" [Emotion: {segment['assigned_emotion']} ({segment['emotion_confidence']:.1f}%)]"
                lang_info = f" [{segment.get('detected_language', '').upper()}]" if multi_language else ""
                
                line = f"[{segment['start']:.2f}s -> {segment['end']:.2f}s] {segment['speaker']}{lang_info}: {segment['text']}{emotion_info}\n"
                f.write(line)
        
        # Save emotion results separately
        emotion_csv = f"{output_prefix}_emotions.csv"
        emotion_df = pd.DataFrame(emotion_results)
        if not emotion_df.empty:
            csv_df = emotion_df.drop('all_emotions', axis=1)
            csv_df.to_csv(emotion_csv, index=False)
        
        # Generate summary
        self.generate_summary(enhanced_transcriptions, emotion_results)
        
        print(f"\n=== ANALYSIS COMPLETE ===")
        print(f"Enhanced transcription: {output_json}")
        print(f"Readable transcript: {output_txt}")
        print(f"Emotion data: {emotion_csv}")
        
        return enhanced_transcriptions

    def generate_summary(self, enhanced_transcriptions, emotion_results):
        """Generate a comprehensive summary of the analysis"""
        print("\n" + "="*50)
        print("ANALYSIS SUMMARY")
        print("="*50)
        
        # Transcription summary
        speaker_text = defaultdict(str)
        speaker_segments = defaultdict(int)
        emotion_distribution = defaultdict(int)
        
        for segment in enhanced_transcriptions:
            speaker = segment['speaker']
            speaker_text[speaker] += segment['text'] + " "
            speaker_segments[speaker] += 1
            emotion_distribution[segment['assigned_emotion']] += 1
        
        print(f"\nTranscription Summary:")
        print(f"Total segments: {len(enhanced_transcriptions)}")
        for speaker, count in speaker_segments.items():
            print(f"  {speaker}: {count} segments")
        
        # Emotion summary
        print(f"\nEmotion Analysis Summary:")
        print(f"Emotion frames analyzed: {len(emotion_results)}")
        print("Emotion distribution in transcription:")
        for emotion, count in emotion_distribution.items():
            percentage = (count / len(enhanced_transcriptions)) * 100
            print(f"  {emotion}: {count} segments ({percentage:.1f}%)")
        
        # Most common emotions by speaker
        print(f"\nEmotions by Speaker:")
        for speaker in speaker_segments.keys():
            speaker_emotions = [s['assigned_emotion'] for s in enhanced_transcriptions if s['speaker'] == speaker]
            if speaker_emotions:
                emotion_count = defaultdict(int)
                for emotion in speaker_emotions:
                    emotion_count[emotion] += 1
                
                most_common = max(emotion_count.items(), key=lambda x: x[1])
                print(f"  {speaker}: {most_common[0]} ({most_common[1]} segments)")

def main():
    """Example usage of the combined analyzer"""
    
    # Initialize analyzer
    analyzer = EmotionTranscriptionAnalyzer()
    
    # Configuration
    AUDIO_FILE1 = r"C:\Users\ASUS\Downloads\audioYoussefDammak11313141200.m4a"
    AUDIO_FILE2 = r"C:\Users\ASUS\Downloads\audioyassinechtourou21313141200.m4a"
    VIDEO_FILE = r"C:\Users\ASUS\Downloads\video1313141200.mp4"
    
    # Transcription settings
    LANGUAGE = None  # Auto-detect language
    MULTI_LANGUAGE = True  # Enable multi-language detection
    
    try:
        # Perform complete analysis
        results = analyzer.analyze_complete_session(
            audio_file1=AUDIO_FILE1,
            audio_file2=AUDIO_FILE2,
            video_file=VIDEO_FILE,
            output_prefix="combined_analysis",
            language=LANGUAGE,
            multi_language=MULTI_LANGUAGE,
            frame_interval=30
        )
        
        print("\nAnalysis completed successfully!")
        
    except Exception as e:
        print(f"Error during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()