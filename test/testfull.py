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
    def __init__(self):
        """
        Initialize the analyzer with both Whisper and DeepFace models
        Always uses large model
        """
        print("Initializing models...")
        
        # Load Whisper model for audio transcription - ALWAYS LARGE
        print("Loading Whisper large model...")
        self.whisper_model = whisper.load_model("large")
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
    
    def analyze_video_emotions(self, video_path: str) -> List[Dict]:
        """
        Analyze emotions in a video and return results with timestamps
        
        Args:
            video_path (str): Path to input video file
            
        Returns:
            list: List of dictionaries containing emotions and timestamps
        """
        print("Starting video emotion analysis...")
        
        # ALWAYS use frame interval 10
        frame_interval = 10
        
        # Open video file
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError("Error: Could not open video file")
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        print(f"Video FPS: {fps}")
        print(f"Total frames: {total_frames}")
        print(f"Frame interval: {frame_interval}")
        
        results = []
        frame_count = 0
        
        while True:
            ret, frame = cap.read()
            
            if not ret:
                break
                
            # Process frame at specified interval - ALWAYS 10
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
    
    def format_conversation(self, merged_segments: List[Dict]) -> List[Dict]:
        """
        Format the conversation with proper grouping and timing
        ALWAYS uses minimum gap of 2.0 seconds
        """
        min_gap = 2.0  # ALWAYS use minimum gap 2.0
        
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

    def analyze_complete_conversation(self, audio_file1: str, audio_file2: str, video_file: str, 
                                   speaker1: str = "Interviewer", speaker2: str = "Interviewee"):
        """
        Complete analysis pipeline for conversation with emotions
        Always uses large model, min gap 2, frame interval 10
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
        emotion_data = self.analyze_video_emotions(video_file)
        
        # Step 3: Merge conversation
        print("\n=== STEP 3: Merging Conversation ===")
        merged_conversation = self.merge_conversation(segments1, segments2)
        
        # Step 4: Assign emotions to conversation
        print("\n=== STEP 4: Assigning Emotions to Conversation ===")
        conversation_with_emotions = self.assign_emotions_to_conversation(merged_conversation, emotion_data)
        
        # Step 5: Format final conversation
        print("\n=== STEP 5: Formatting Final Conversation ===")
        final_conversation = self.format_conversation(conversation_with_emotions)
        
        return final_conversation

def full_transcription_and_emotion_analysis(
    audio1: str,
    audio2: str,
    video: str,
    speaker1: str = "Interviewer",
    speaker2: str = "Interviewee"
):

    try:
        # Initialize analyzer - ALWAYS uses large model
        analyzer = ConversationEmotionAnalyzer()
        
        # Run complete analysis - ALWAYS uses min gap 2 and frame interval 10
        final_conversation = analyzer.analyze_complete_conversation(
            audio_file1=audio1,
            audio_file2=audio2,
            video_file=video,
            speaker1=speaker1,
            speaker2=speaker2
        )
    
    # ALWAYS return JSON data directly
        print("\n" + "=" * 70)
        print("COMPLETE CONVERSATION ANALYSIS WITH EMOTIONS")
        print("=" * 70)
        print(json.dumps(final_conversation, indent=2, ensure_ascii=False))
        
        print(f"\n✅ Analysis complete! Processed {len(final_conversation)} conversation turns.")
        print("Note: Emotion analysis is assigned to the speaker who appears in the video.")

        return final_conversation
    
    except Exception as e:
        print(f"❌ Error during analysis: {str(e)}")
        return None