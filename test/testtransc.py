"""
Multi-Language Audio Transcription Script

This script can transcribe audio files in different ways:
1. Single language (specify LANGUAGE = "en", "fr", "ar", etc.)
2. Multi-language detection (set MULTI_LANGUAGE = True)
3. Auto-detect language (set LANGUAGE = None)

For multi-language conversations, set MULTI_LANGUAGE = True
"""

import whisper
import json
import os
from pydub import AudioSegment
import logging

# Set up logging to see Whisper warnings
logging.basicConfig(level=logging.WARNING)

def get_audio_duration(path):
    """Return duration in seconds using pydub."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Audio file not found: {path}")
    audio = AudioSegment.from_file(path)
    return len(audio) / 1000.0  # milliseconds → seconds

def transcribe_with_timestamps(audio_path, model, speaker_name, language=None, multi_language=False):
    """
    Transcribe audio with timestamps
    
    Args:
        audio_path: Path to audio file
        model: Whisper model
        speaker_name: Name of speaker for labeling
        language: Specific language code (e.g., "en", "fr")
        multi_language: Whether to enable multi-language detection
    """
    
    if multi_language:
        # Enable multi-language detection
        result = model.transcribe(audio_path, language=None, task="transcribe")
    elif language:
        # Use specified language
        result = model.transcribe(audio_path, language=language)
    else:
        # Auto-detect language (single language)
        result = model.transcribe(audio_path)
    
    segments = []
    for seg in result["segments"]:
        segment_data = {
            "start": seg["start"],
            "end": seg["end"],
            "text": seg["text"].strip(),
            "speaker": speaker_name
        }
        
        # Add detected language if multi-language mode is enabled
        if multi_language and "language" in seg:
            segment_data["detected_language"] = seg["language"]
        elif multi_language:
            # If language info isn't in segments, get it from the main result
            segment_data["detected_language"] = result.get("language", "unknown")
        
        segments.append(segment_data)
    
    return segments, result.get("language", "unknown") if multi_language else language

def merge_conversations(segments):
    """Merge and sort segments by start time"""
    merged = sorted(segments, key=lambda x: x["start"])
    return merged

def format_output_segment(seg, show_language=False):
    """Format a single segment for output"""
    if show_language and "detected_language" in seg:
        lang_info = f" [{seg['detected_language'].upper()}]"
    else:
        lang_info = ""
    
    return f"[{seg['start']:.2f}s -> {seg['end']:.2f}s] {seg['speaker']}{lang_info}: {seg['text']}"

if __name__ == "__main__":
    
    # ===== CONFIGURATION =====
    # Choose ONE of the following options:
    
    # Option 1: Single language transcription
    # LANGUAGE = "en"  # English
    # LANGUAGE = "fr"  # French  
    # LANGUAGE = "ar"  # Arabic
    # MULTI_LANGUAGE = False
    
    # Option 2: Auto-detect language (single language per file)
    # LANGUAGE = None
    # MULTI_LANGUAGE = False
    
    # Option 3: Multi-language detection (for conversations in multiple languages)
    LANGUAGE = None  # Must be None for multi-language detection to work properly
    MULTI_LANGUAGE = True
    
    # File paths
    file1 = r"C:\Users\yassine\Documents\Zoom\2025-10-12 18.10.27 Mouhamed Yassine Chtourou's Zoom Meeting\Audio Record\audioMouhamedYassineC11624140658.m4a"
    file2 = r"C:\Users\yassine\Documents\Zoom\2025-10-12 18.10.27 Mouhamed Yassine Chtourou's Zoom Meeting\Audio Record\audioYoussefDammak21624140658.m4a"
    
    # Check if files exist
    if not os.path.exists(file1) or not os.path.exists(file2):
        print("Audio files not found!")
        print(f"Looking for:")
        print(f"  - {file1}")
        print(f"  - {file2}")
        print("\nTo use this script:")
        print("1. Add your audio files to the test directory, or")
        print("2. Update the file paths in this script to point to your audio files")
        print("\nSupported audio formats: .mp3, .wav, .m4a, .flac, .ogg, etc.")
        exit(1)
    
    print("Loading Whisper model...")
    model = whisper.load_model("large")
    print("Model loaded successfully!")

    print("Analyzing audio files...")
    try:
        dur1 = get_audio_duration(file1)
        dur2 = get_audio_duration(file2)
        
        print(f"File 1: {os.path.basename(file1)} ({dur1:.2f}s)")
        print(f"File 2: {os.path.basename(file2)} ({dur2:.2f}s)")
        
        if dur1 >= dur2:
            main_file, second_file = file1, file2
            main_speaker, second_speaker = "Speaker 1", "Speaker 2"
        else:
            main_file, second_file = file2, file1
            main_speaker, second_speaker = "Speaker 1", "Speaker 2"

        print(f"\n{main_speaker} is the longer file ({max(dur1, dur2):.2f}s).")

        # Determine transcription mode
        if MULTI_LANGUAGE:
            print("Transcribing audio files with multi-language detection...")
            main_segments, main_lang = transcribe_with_timestamps(main_file, model, main_speaker, 
                                                                language=LANGUAGE, multi_language=True)
            second_segments, second_lang = transcribe_with_timestamps(second_file, model, second_speaker, 
                                                                    language=LANGUAGE, multi_language=True)
            
            print(f"Detected languages - {main_speaker}: {main_lang}, {second_speaker}: {second_lang}")
        else:
            lang_display = LANGUAGE.upper() if LANGUAGE else "AUTO-DETECTED"
            print(f"Transcribing audio files in {lang_display}...")
            main_segments, _ = transcribe_with_timestamps(main_file, model, main_speaker, 
                                                        language=LANGUAGE, multi_language=False)
            second_segments, _ = transcribe_with_timestamps(second_file, model, second_speaker, 
                                                          language=LANGUAGE, multi_language=False)

        merged_segments = merge_conversations(main_segments + second_segments)

        print("\nMerged conversation:")
        print("=" * 50)
        for seg in merged_segments:
            print(format_output_segment(seg, show_language=MULTI_LANGUAGE))

        # Save results
        output_file = "merged_conversation_ordered.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(merged_segments, f, ensure_ascii=False, indent=2)
        
        # Also save a readable text version
        text_output_file = "merged_conversation_readable.txt"
        with open(text_output_file, "w", encoding="utf-8") as f:
            f.write("Merged Conversation Transcript\n")
            f.write("=" * 50 + "\n")
            for seg in merged_segments:
                f.write(format_output_segment(seg, show_language=MULTI_LANGUAGE) + "\n")
        
        print(f"\nConversation saved to: {output_file} (JSON) and {text_output_file} (readable)")
        print("Transcription completed successfully!")
        
    except Exception as e:
        print(f"Error during processing: {e}")
        import traceback
        traceback.print_exc()
        exit(1)