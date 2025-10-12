import cv2
from deepface import DeepFace
import pandas as pd
from datetime import datetime
import whisper
import json
import os
from pydub import AudioSegment
import logging
import numpy as np

# Set up logging to see Whisper warnings
logging.basicConfig(level=logging.WARNING)

class ConversationAnalyzer:
    def __init__(self):
        self.whisper_model = None
        self.emotion_results = []
        self.transcription_results = []
        self.combined_results = []
    
    def load_models(self):
        """Load both Whisper and DeepFace models"""
        print("Loading Whisper model...")
        self.whisper_model = whisper.load_model("small")
        print("Whisper model loaded successfully!")
        # DeepFace doesn't need explicit loading
    
    def get_audio_duration(self, path):
        """Return duration in seconds using pydub."""
        if not os.path.exists(path):
            raise FileNotFoundError(f"Audio file not found: {path}")
        audio = AudioSegment.from_file(path)
        return len(audio) / 1000.0  # milliseconds → seconds
    
    def transcribe_with_timestamps(self, audio_path, speaker_name, language=None, multi_language=False):
        """
        Transcribe audio with timestamps
        
        Args:
            audio_path: Path to audio file
            speaker_name: Name of speaker for labeling
            language: Specific language code (e.g., "en", "fr")
            multi_language: Whether to enable multi-language detection
        """
        
        if multi_language:
            # Enable multi-language detection
            result = self.whisper_model.transcribe(audio_path, language=None, task="transcribe")
        elif language:
            # Use specified language
            result = self.whisper_model.transcribe(audio_path, language=language)
        else:
            # Auto-detect language (single language)
            result = self.whisper_model.transcribe(audio_path)
        
        segments = []
        for seg in result["segments"]:
            segment_data = {
                "start": float(seg["start"]),  # Convert to regular float
                "end": float(seg["end"]),      # Convert to regular float
                "text": seg["text"].strip(),
                "speaker": speaker_name,
                "type": "speech"
            }
            
            # Add detected language if multi-language mode is enabled
            if multi_language and "language" in seg:
                segment_data["detected_language"] = seg["language"]
            elif multi_language:
                # If language info isn't in segments, get it from the main result
                segment_data["detected_language"] = result.get("language", "unknown")
            
            segments.append(segment_data)
        
        return segments, result.get("language", "unknown") if multi_language else language
    
    def analyze_video_emotions(self, video_path, frame_interval=30):
        """
        Analyze emotions in a video and return results with timestamps
        
        Args:
            video_path (str): Path to input video file
            frame_interval (int): Analyze every nth frame (higher = faster processing)
        
        Returns:
            list: List of dictionaries containing emotions and timestamps
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
                    timestamp = float(frame_count / fps)  # Convert to regular float
                    
                    # Format timestamp
                    time_str = str(datetime.utcfromtimestamp(timestamp).strftime('%H:%M:%S.%f')[:-3])
                    
                    # Get dominant emotion
                    emotions = analysis[0]['emotion']
                    dominant_emotion = max(emotions.items(), key=lambda x: x[1])
                    
                    # Convert all emotion values to regular floats
                    emotions_clean = {k: float(v) for k, v in emotions.items()}
                    
                    result = {
                        "frame": frame_count,
                        "timestamp": timestamp,
                        "timestamp_formatted": time_str,
                        "dominant_emotion": dominant_emotion[0],
                        "emotion_confidence": float(dominant_emotion[1]),  # Convert to regular float
                        "all_emotions": emotions_clean,
                        "type": "emotion"
                    }
                    
                    results.append(result)
                    
                    print(f"Frame {frame_count} ({time_str}): {dominant_emotion[0]} ({dominant_emotion[1]:.2f}%)")
                    
                except Exception as e:
                    print(f"Error processing frame {frame_count}: {str(e)}")
                    # Add entry even if analysis fails
                    timestamp = float(frame_count / fps)  # Convert to regular float
                    time_str = str(datetime.utcfromtimestamp(timestamp).strftime('%H:%M:%S.%f')[:-3])
                    
                    results.append({
                        "frame": frame_count,
                        "timestamp": timestamp,
                        "timestamp_formatted": time_str,
                        "dominant_emotion": "unknown",
                        "emotion_confidence": 0.0,
                        "all_emotions": {},
                        "type": "emotion"
                    })
            
            frame_count += 1
        
        cap.release()
        
        print(f"Emotion analysis complete! Processed {len(results)} frames")
        return results
    
    def merge_conversations(self, segments):
        """Merge and sort segments by start time"""
        merged = sorted(segments, key=lambda x: x["start"])
        return merged
    
    def find_emotion_at_time(self, timestamp, tolerance=2.0):
        """
        Find the closest emotion analysis to a given timestamp
        
        Args:
            timestamp: Time to find emotion for
            tolerance: Maximum time difference in seconds to accept
        
        Returns:
            dict: Emotion data or None if not found within tolerance
        """
        closest_emotion = None
        min_diff = float('inf')
        
        for emotion in self.emotion_results:
            diff = abs(emotion['timestamp'] - timestamp)
            if diff < min_diff and diff <= tolerance:
                min_diff = diff
                closest_emotion = emotion
        
        return closest_emotion
    
    def combine_analysis(self, transcription_segments, video_speaker):
        """
        Combine transcription and emotion analysis
        
        Args:
            transcription_segments: List of transcription segments
            video_speaker: Name of the speaker in the video (for emotion assignment)
        """
        combined = []
        
        for segment in transcription_segments:
            # Find emotion at the start time of the speech segment
            emotion_data = self.find_emotion_at_time(segment['start'])
            
            combined_segment = segment.copy()
            
            if emotion_data and segment['speaker'] == video_speaker:
                combined_segment['dominant_emotion'] = emotion_data['dominant_emotion']
                combined_segment['emotion_confidence'] = float(emotion_data['emotion_confidence'])  # Convert to float
                combined_segment['emotion_timestamp'] = float(emotion_data['timestamp']) if emotion_data['timestamp'] else None
                combined_segment['emotion_frame'] = emotion_data['frame']
            else:
                combined_segment['dominant_emotion'] = 'unknown'
                combined_segment['emotion_confidence'] = 0.0
                combined_segment['emotion_timestamp'] = None
                combined_segment['emotion_frame'] = None
            
            combined.append(combined_segment)
        
        return combined
    
    def format_output_segment(self, seg, show_language=False, show_emotion=True):
        """Format a single segment for output"""
        if show_language and "detected_language" in seg:
            lang_info = f" [{seg['detected_language'].upper()}]"
        else:
            lang_info = ""
        
        emotion_info = ""
        if show_emotion and seg.get('dominant_emotion') and seg['dominant_emotion'] != 'unknown':
            emotion_info = f" | Emotion: {seg['dominant_emotion']} ({seg['emotion_confidence']:.1f}%)"
        
        return f"[{seg['start']:.2f}s -> {seg['end']:.2f}s] {seg['speaker']}{lang_info}: {seg['text']}{emotion_info}"
    
    def print_summary(self):
        """Print a summary of the analysis results"""
        if not self.combined_results:
            print("No results to summarize")
            return
        
        print("\n=== ANALYSIS SUMMARY ===")
        print(f"Total speech segments: {len(self.combined_results)}")
        print(f"Total emotion frames analyzed: {len(self.emotion_results)}")
        
        # Count emotions for the video speaker
        emotion_count = {}
        speech_count = {}
        
        for result in self.combined_results:
            speaker = result['speaker']
            speech_count[speaker] = speech_count.get(speaker, 0) + 1
            
            if result.get('dominant_emotion') and result['dominant_emotion'] != 'unknown':
                emotion = result['dominant_emotion']
                emotion_count[emotion] = emotion_count.get(emotion, 0) + 1
        
        print("\nSpeech distribution by speaker:")
        for speaker, count in speech_count.items():
            percentage = (count / len(self.combined_results)) * 100
            print(f"  {speaker}: {count} segments ({percentage:.1f}%)")
        
        print("\nDetected emotions distribution:")
        total_emotions = sum(emotion_count.values())
        if total_emotions > 0:
            for emotion, count in emotion_count.items():
                percentage = (count / total_emotions) * 100
                print(f"  {emotion}: {count} segments ({percentage:.1f}%)")
            
            # Find most common emotion
            if emotion_count:
                most_common = max(emotion_count.items(), key=lambda x: x[1])
                print(f"\nMost common emotion: {most_common[0]} ({most_common[1]} segments)")
        else:
            print("  No emotions detected in speech segments")

    def convert_to_serializable(self, obj):
        """Convert numpy types to Python native types for JSON serialization"""
        if isinstance(obj, (np.float32, np.float64)):
            return float(obj)
        elif isinstance(obj, (np.int32, np.int64)):
            return int(obj)
        elif isinstance(obj, dict):
            return {key: self.convert_to_serializable(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self.convert_to_serializable(item) for item in obj]
        else:
            return obj

def main():
    # ===== CONFIGURATION =====
    # Audio and video file paths
    audio_file1 = r"C:\Users\yassine\Documents\Zoom\2025-10-12 18.10.27 Mouhamed Yassine Chtourou's Zoom Meeting\Audio Record\audioMouhamedYassineC11624140658.m4a"
    audio_file2 = r"C:\Users\yassine\Documents\Zoom\2025-10-12 18.10.27 Mouhamed Yassine Chtourou's Zoom Meeting\Audio Record\audioYoussefDammak21624140658.m4a"
    video_file = r"C:\Users\yassine\Documents\Zoom\2025-10-12 18.10.27 Mouhamed Yassine Chtourou's Zoom Meeting\video1624140658.mp4"
    
    # Speaker configuration
    speaker1_name = "Mouhamed Yassine"
    speaker2_name = "Youssef Dammak"
    video_speaker = speaker1_name  # Which speaker is in the video
    
    # Transcription settings
    LANGUAGE = None  # Set to specific language code or None for auto-detection
    MULTI_LANGUAGE = True  # Enable multi-language detection
    
    # Emotion analysis settings
    FRAME_INTERVAL = 30  # Process every 30th frame for emotion analysis
    
    # Output files
    output_json = "complete_conversation_analysis.json"
    output_text = "complete_conversation_readable.txt"
    output_csv = "conversation_emotions.csv"
    
    # Initialize analyzer
    analyzer = ConversationAnalyzer()
    
    try:
        # Load models
        analyzer.load_models()
        
        # Check if files exist
        if not all(os.path.exists(f) for f in [audio_file1, audio_file2, video_file]):
            print("One or more files not found!")
            print(f"Audio 1: {audio_file1} - {'Exists' if os.path.exists(audio_file1) else 'Missing'}")
            print(f"Audio 2: {audio_file2} - {'Exists' if os.path.exists(audio_file2) else 'Missing'}")
            print(f"Video: {video_file} - {'Exists' if os.path.exists(video_file) else 'Missing'}")
            return
        
        # Get audio durations
        dur1 = analyzer.get_audio_duration(audio_file1)
        dur2 = analyzer.get_audio_duration(audio_file2)
        
        print(f"File 1: {os.path.basename(audio_file1)} ({dur1:.2f}s)")
        print(f"File 2: {os.path.basename(audio_file2)} ({dur2:.2f}s)")
        
        # Determine main speaker based on duration
        if dur1 >= dur2:
            main_file, second_file = audio_file1, audio_file2
            main_speaker, second_speaker = speaker1_name, speaker2_name
        else:
            main_file, second_file = audio_file2, audio_file1
            main_speaker, second_speaker = speaker2_name, speaker1_name
        
        print(f"\n{main_speaker} has the longer audio ({max(dur1, dur2):.2f}s)")
        print(f"Video is assigned to: {video_speaker}")
        
        # Step 1: Transcribe audio files
        print("\n" + "="*50)
        print("STEP 1: Transcribing audio files...")
        
        if MULTI_LANGUAGE:
            print("Transcribing with multi-language detection...")
            main_segments, main_lang = analyzer.transcribe_with_timestamps(main_file, main_speaker, 
                                                                          language=LANGUAGE, multi_language=True)
            second_segments, second_lang = analyzer.transcribe_with_timestamps(second_file, second_speaker, 
                                                                              language=LANGUAGE, multi_language=True)
            
            print(f"Detected languages - {main_speaker}: {main_lang}, {second_speaker}: {second_lang}")
        else:
            lang_display = LANGUAGE.upper() if LANGUAGE else "AUTO-DETECTED"
            print(f"Transcribing in {lang_display}...")
            main_segments, _ = analyzer.transcribe_with_timestamps(main_file, main_speaker, 
                                                                  language=LANGUAGE, multi_language=False)
            second_segments, _ = analyzer.transcribe_with_timestamps(second_file, second_speaker, 
                                                                    language=LANGUAGE, multi_language=False)
        
        # Merge transcriptions
        analyzer.transcription_results = analyzer.merge_conversations(main_segments + second_segments)
        print(f"Transcription complete! Found {len(analyzer.transcription_results)} speech segments.")
        
        # Step 2: Analyze video emotions
        print("\n" + "="*50)
        print("STEP 2: Analyzing video emotions...")
        analyzer.emotion_results = analyzer.analyze_video_emotions(video_file, frame_interval=FRAME_INTERVAL)
        
        # Step 3: Combine analysis
        print("\n" + "="*50)
        print("STEP 3: Combining transcription and emotion analysis...")
        analyzer.combined_results = analyzer.combine_analysis(analyzer.transcription_results, video_speaker)
        
        # Step 4: Output results
        print("\n" + "="*50)
        print("FINAL COMBINED CONVERSATION WITH EMOTIONS:")
        print("="*50)
        
        for seg in analyzer.combined_results:
            print(analyzer.format_output_segment(seg, show_language=MULTI_LANGUAGE, show_emotion=True))
        
        # Save results - Convert to serializable format first
        print("\nSaving results...")
        serializable_results = analyzer.convert_to_serializable(analyzer.combined_results)
        
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(serializable_results, f, ensure_ascii=False, indent=2)
        
        with open(output_text, "w", encoding="utf-8") as f:
            f.write("Complete Conversation Analysis with Emotions\n")
            f.write("=" * 60 + "\n")
            for seg in analyzer.combined_results:
                f.write(analyzer.format_output_segment(seg, show_language=MULTI_LANGUAGE, show_emotion=True) + "\n")
        
        # Save CSV with emotions
        if analyzer.combined_results:
            csv_data = []
            for seg in analyzer.combined_results:
                row = {
                    'speaker': seg['speaker'],
                    'start_time': seg['start'],
                    'end_time': seg['end'],
                    'text': seg['text'],
                    'dominant_emotion': seg.get('dominant_emotion', 'unknown'),
                    'emotion_confidence': seg.get('emotion_confidence', 0),
                    'emotion_timestamp': seg.get('emotion_timestamp', ''),
                    'in_video': 'Yes' if seg['speaker'] == video_speaker else 'No'
                }
                if MULTI_LANGUAGE and 'detected_language' in seg:
                    row['language'] = seg['detected_language']
                csv_data.append(row)
            
            df = pd.DataFrame(csv_data)
            df.to_csv(output_csv, index=False)
            print(f"CSV data saved to: {output_csv}")
        
        print(f"JSON results saved to: {output_json}")
        print(f"Readable transcript saved to: {output_text}")
        
        # Print summary
        analyzer.print_summary()
        
        print("\nAnalysis completed successfully!")
        
    except Exception as e:
        print(f"Error during processing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()