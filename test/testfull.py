#!/usr/bin/env python3
"""
Combined Audio Transcription and Video Emotion Analysis Script
Analyzes two audio files for conversation and one video for emotions of the speaking person
"""

import cv2
import os
import json
import argparse
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import whisper
from deepface import DeepFace
from types import SimpleNamespace

class ConversationEmotionAnalyzer:
    def __init__(self, whisper_model_size: str = "large"):
        """
        Initialize the analyzer with both Whisper and DeepFace models
        
        Args:
            whisper_model_size: Whisper model size ("tiny", "base", "small", "medium", "large")
        """
        print("Initializing models...")
        
        # Load Whisper model for audio transcription
        print(f"Loading Whisper {whisper_model_size} model...")
        self.whisper_model = whisper.load_model(whisper_model_size)
        print("Whisper model loaded successfully!")
        
        # DeepFace doesn't require explicit model loading
        print("DeepFace emotion analysis ready!")
    
    def transcribe_audio(self, audio_path: str, speaker_name: str = "Speaker") -> List[Dict]:
        """
        Transcribe a single audio file and return segments with timestamps
        Forces transcription to English using Whisper's translation feature
        
        Args:
            audio_path: Path to audio file
            speaker_name: Name to identify the speaker
            
        Returns:
            List of segments with text, start, end timestamps and speaker
        """
        print(f"Transcribing {speaker_name}'s audio to English...")
        
        # Transcribe with translation to English
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
    
    def analyze_video_emotions(self, video_path: str, frame_interval: int = 10) -> List[Dict]:
        """
        Analyze emotions in a video and return results with timestamps
        
        Args:
            video_path (str): Path to input video file
            frame_interval (int): Analyze every nth frame (higher = faster processing)
            
        Returns:
            list: List of dictionaries containing emotions and timestamps
        """
        print("Starting video emotion analysis...")
        
        # Open video file
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError("Error: Could not open video file")
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        print(f"Video FPS: {fps}")
        print(f"Total frames: {total_frames}")
        
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
                    
                    # Get dominant emotion and all emotions
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
        print(f"Video emotion analysis complete! Processed {len(results)} frames")
        return results
    
    def merge_conversation(self, segments1: List[Dict], segments2: List[Dict]) -> List[Dict]:
        """
        Merge segments from two speakers by timestamp to create conversation flow
        """
        # Combine all segments
        all_segments = segments1 + segments2
        
        # Sort by start time
        all_segments.sort(key=lambda x: x["start"])
        
        return all_segments
    
    def assign_emotions_to_conversation(self, conversation: List[Dict], emotion_data: List[Dict]) -> List[Dict]:
        """
        Assign emotion data to conversation segments based on timestamps
        
        Args:
            conversation: Merged conversation segments
            emotion_data: Video emotion analysis results
            
        Returns:
            Conversation with assigned emotions
        """
        print("Assigning emotions to conversation segments...")
        
        for segment in conversation:
            segment_start = segment["start"]
            segment_end = segment["end"]
            
            # Find emotions that occur during this conversation segment
            segment_emotions = []
            for emotion in emotion_data:
                if segment_start <= emotion["timestamp"] <= segment_end:
                    segment_emotions.append(emotion)
            
            # Calculate dominant emotion for this segment
            if segment_emotions:
                # Count emotion occurrences
                emotion_counts = {}
                emotion_confidences = {}
                
                for emo in segment_emotions:
                    emotion = emo["dominant_emotion"]
                    if emotion != "unknown":
                        emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
                        emotion_confidences[emotion] = emotion_confidences.get(emotion, 0) + emo["emotion_confidence"]
                
                if emotion_counts:
                    # Find most frequent emotion
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
        """
        Format the conversation with proper grouping and timing
        """
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
            
            # If same speaker and gap is small, merge the segments
            if (segment["speaker"] == current_speaker and 
                segment["start"] - current_end < min_gap):
                current_text += " " + segment["text"]
                current_end = segment["end"]
                current_emotions.append(segment.get("emotion", "unknown"))
            else:
                # Calculate dominant emotion for this merged segment
                if current_emotions:
                    emotion_counts = {}
                    for emotion in current_emotions:
                        if emotion != "unknown":
                            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
                    
                    dominant_emotion = max(emotion_counts.items(), key=lambda x: x[1])[0] if emotion_counts else "unknown"
                else:
                    dominant_emotion = "unknown"
                
                # Add the current segment to formatted list
                formatted.append({
                    "speaker": current_speaker,
                    "text": current_text,
                    "start": current_start,
                    "end": current_end,
                    "duration": current_end - current_start,
                    "emotion": dominant_emotion,
                    "emotion_samples": len(current_emotions)
                })
                
                # Start new segment
                current_speaker = segment["speaker"]
                current_text = segment["text"]
                current_start = segment["start"]
                current_end = segment["end"]
                current_emotions = [segment.get("emotion", "unknown")]
        
        # Add the last segment
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
    
    def save_complete_analysis(self, conversation: List[Dict], output_format: str = "both"):
        """
        Save complete conversation analysis with emotions
        """
        base_name = "conversation_emotion_analysis"
        
        if output_format in ["text", "both"]:
            txt_filename = f"{base_name}.txt"
            with open(txt_filename, "w", encoding="utf-8") as f:
                f.write("COMPLETE CONVERSATION ANALYSIS WITH EMOTIONS\n")
                f.write("=" * 70 + "\n\n")
                
                for i, turn in enumerate(conversation, 1):
                    start_time = str(timedelta(seconds=int(turn["start"])))
                    emotion_info = f" [{turn['emotion']}]" if turn.get('emotion') and turn['emotion'] != 'unknown' else " [No emotion data]"
                    
                    f.write(f"Turn {i} [{start_time}]{emotion_info}:\n")
                    f.write(f"{turn['speaker']}: {turn['text']}\n\n")
            
            print(f"Text analysis saved to: {txt_filename}")
        
        if output_format in ["json", "both"]:
            json_filename = f"{base_name}.json"
            with open(json_filename, "w", encoding="utf-8") as f:
                json.dump(conversation, f, indent=2, ensure_ascii=False)
            
            print(f"JSON analysis saved to: {json_filename}")
        
        if output_format in ["csv", "both"]:
            csv_filename = f"{base_name}.csv"
            # Create a simplified DataFrame for CSV
            csv_data = []
            for turn in conversation:
                csv_data.append({
                    'turn_number': conversation.index(turn) + 1,
                    'speaker': turn['speaker'],
                    'start_time': turn['start'],
                    'end_time': turn['end'],
                    'duration': turn['duration'],
                    'text': turn['text'],
                    'emotion': turn.get('emotion', 'unknown'),
                    'emotion_samples': turn.get('emotion_samples', 0)
                })
            
            df = pd.DataFrame(csv_data)
            df.to_csv(csv_filename, index=False)
            print(f"CSV analysis saved to: {csv_filename}")
    
    def print_complete_analysis(self, conversation: List[Dict]):
        """
        Print the complete conversation analysis with emotions
        """
        print("\n" + "=" * 70)
        print("COMPLETE CONVERSATION ANALYSIS WITH EMOTIONS")
        print("=" * 70)
        
        for i, turn in enumerate(conversation, 1):
            start_time = str(timedelta(seconds=int(turn["start"])))
            emotion_info = f" [{turn['emotion']}]" if turn.get('emotion') and turn['emotion'] != 'unknown' else " [No emotion data]"
            
            print(f"\nTurn {i} [{start_time}]{emotion_info}:")
            print(f"{turn['speaker']}: {turn['text']}")
    
    def analyze_complete_conversation(self, audio_file1: str, audio_file2: str, video_file: str, 
                                   speaker1: str = "Interviewer", speaker2: str = "Interviewee",
                                   whisper_model: str = "large", output_format: str = "both",
                                   merge_gap: float = 2.0, frame_interval: int = 10):
        """
        Complete analysis pipeline for conversation with emotions
        """
        # Validate input files
        for file_path in [audio_file1, audio_file2, video_file]:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
        
        # Step 1: Transcribe both audio files
        print("=== STEP 1: Audio Transcription ===")
        segments1 = self.transcribe_audio(audio_file1, speaker1)
        segments2 = self.transcribe_audio(audio_file2, speaker2)
        
        # Step 2: Analyze video emotions
        print("\n=== STEP 2: Video Emotion Analysis ===")
        emotion_data = self.analyze_video_emotions(video_file, frame_interval)
        
        # Step 3: Merge conversation
        print("\n=== STEP 3: Merging Conversation ===")
        merged_conversation = self.merge_conversation(segments1, segments2)
        
        # Step 4: Assign emotions to conversation
        print("\n=== STEP 4: Assigning Emotions to Conversation ===")
        conversation_with_emotions = self.assign_emotions_to_conversation(merged_conversation, emotion_data)
        
        # Step 5: Format final conversation
        print("\n=== STEP 5: Formatting Final Conversation ===")
        final_conversation = self.format_conversation(conversation_with_emotions, merge_gap)
        
        return final_conversation

def main():
    print("=== Complete Conversation & Emotion Analysis ===")
    print("This script analyzes two audio files and one video to create a complete conversation transcript with emotions.\n")
    
    # Get user input
    audio_file1 = input("Enter path to first audio file (Interviewer): ").strip().strip('"')
    audio_file2 = input("Enter path to second audio file (Interviewee): ").strip().strip('"')
    video_file = input("Enter path to video file (for emotion analysis): ").strip().strip('"')

    speaker1 = input("Enter name for first speaker [default: Interviewer]: ").strip() or "Interviewer"
    speaker2 = input("Enter name for second speaker [default: Interviewee]: ").strip() or "Interviewee"

    whisper_model = input("Enter Whisper model size (tiny/base/small/medium/large) [default: large]: ").strip() or "large"
    output_format = input("Choose output format (text/json/csv/both) [default: both]: ").strip() or "both"
    
    try:
        merge_gap = float(input("Enter minimum gap in seconds to merge segments [default: 2.0]: ").strip() or 2.0)
    except ValueError:
        merge_gap = 2.0
    
    try:
        frame_interval = int(input("Enter frame interval for emotion analysis (higher = faster) [default: 10]: ").strip() or 10)
    except ValueError:
        frame_interval = 10
    
    try:
        # Initialize analyzer
        analyzer = ConversationEmotionAnalyzer(whisper_model_size=whisper_model)
        
        # Run complete analysis
        final_conversation = analyzer.analyze_complete_conversation(
            audio_file1=audio_file1,
            audio_file2=audio_file2,
            video_file=video_file,
            speaker1=speaker1,
            speaker2=speaker2,
            whisper_model=whisper_model,
            output_format=output_format,
            merge_gap=merge_gap,
            frame_interval=frame_interval
        )
        
        # Display and save results
        analyzer.print_complete_analysis(final_conversation)
        analyzer.save_complete_analysis(final_conversation, output_format)
        
        print(f"\n✅ Analysis complete! Processed {len(final_conversation)} conversation turns.")
        print("Note: Emotion analysis is assigned to the speaker who appears in the video.")
        
    except Exception as e:
        print(f"❌ Error during analysis: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())