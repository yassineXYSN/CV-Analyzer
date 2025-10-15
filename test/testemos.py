import cv2
from deepface import DeepFace
import pandas as pd
from datetime import datetime

def analyze_video_emotions(video_path, output_csv=None, frame_interval=30):
    """
    Analyze emotions in a video and return results with timestamps
    
    Args:
        video_path (str): Path to input video file
        output_csv (str): Path to output CSV file (optional)
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
    
    # Save to CSV if requested
    if output_csv and results:
        df = pd.DataFrame(results)
        # Clean up DataFrame for CSV output
        csv_df = df.drop('all_emotions', axis=1)
        csv_df.to_csv(output_csv, index=False)
        print(f"\nResults saved to {output_csv}")
    
    print(f"\nAnalysis complete! Processed {len(results)} frames")
    return results

def print_summary(results):
    """Print a summary of the analysis results"""
    if not results:
        print("No results to summarize")
        return
    
    print("\n=== ANALYSIS SUMMARY ===")
    print(f"Total frames analyzed: {len(results)}")
    
    # Count emotions
    emotion_count = {}
    for result in results:
        emotion = result['dominant_emotion']
        emotion_count[emotion] = emotion_count.get(emotion, 0) + 1
    
    print("\nDominant emotions distribution:")
    for emotion, count in emotion_count.items():
        percentage = (count / len(results)) * 100
        print(f"  {emotion}: {count} frames ({percentage:.1f}%)")
    
    # Find most common emotion
    if emotion_count:
        most_common = max(emotion_count.items(), key=lambda x: x[1])
        print(f"\nMost common emotion: {most_common[0]} ({most_common[1]} frames)")

if __name__ == "__main__":
    # Example usage
    video_file = r"C:\Users\ASUS\Downloads\635eb8d4-5f03-4590-8695-96e783a61e65.mp4"  # Change to your video path
    output_file = "emotion_results.csv"
    
    try:
        # Analyze video
        results = analyze_video_emotions(
            video_path=video_file,
            output_csv=output_file,
            frame_interval=30  # Process every 30th frame
        )
        
        # Print summary
        print_summary(results)
        
    except Exception as e:
        print(f"Error: {str(e)}")