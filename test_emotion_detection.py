"""
Test script for emotion detection functionality (FastAPI version)
"""
import cv2
import requests
import time

def test_camera_access():
    """Test if camera is accessible"""
    print("Testing camera access...")
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("❌ Camera not accessible")
        return False

    ret, frame = cap.read()
    if ret:
        print("✅ Camera is working")
        print(f"Frame shape: {frame.shape}")
    else:
        print("❌ Cannot read from camera")
        return False

    cap.release()
    return True

def test_face_detection():
    """Test face detection functionality"""
    print("\nTesting face detection...")

    # Load face cascade
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    if face_cascade.empty():
        print("❌ Face cascade not loaded")
        return False

    print("✅ Face cascade loaded successfully")

    # Test with camera
    cap = cv2.VideoCapture(0)

    for i in range(10):  # Test 10 frames
        ret, frame = cap.read()
        if ret:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)

            if len(faces) > 0:
                print(f"✅ Frame {i+1}: {len(faces)} face(s) detected")
            else:
                print(f"⚠️  Frame {i+1}: No faces detected")

        time.sleep(0.1)

    cap.release()
    return True

def test_api_endpoints():
    """Test FastAPI endpoints"""
    print("\nTesting API endpoints...")
    base_url = "http://127.0.0.1:8000/interview"

    # Test start session
    try:
        response = requests.post(f"{base_url}/start_session",
                                 json={
                                     "candidate_name": "Test Candidate",
                                     "interviewer_name": "Test Interviewer"
                                 })

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Start session endpoint working")
                session_id = data.get('session_id')
            else:
                print("❌ Start session failed:", data.get('message'))
                return False
        else:
            print(f"❌ Start session endpoint error: {response.status_code}")
            return False

    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to FastAPI server. Make sure it's running on localhost:8000")
        return False

    # Test live stats
    try:
        response = requests.get(f"{base_url}/get_live_stats")
        if response.status_code == 200:
            print("✅ Live stats endpoint working")
        else:
            print(f"❌ Live stats endpoint error: {response.status_code}")
    except Exception as e:
        print(f"❌ Live stats endpoint error: {e}")

    # Test end session
    try:
        response = requests.post(f"{base_url}/end_session")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ End session endpoint working")
                print("✅ Report generated successfully")
            else:
                print("❌ End session failed:", data.get('message'))
        else:
            print(f"❌ End session endpoint error: {response.status_code}")
    except Exception as e:
        print(f"❌ End session endpoint error: {e}")

    return True

def run_full_test():
    """Run complete test suite"""
    print("🧪 Starting Emotion Detection System Tests (FastAPI)\n")
    print("=" * 50)

    # Test 1: Camera access
    camera_ok = test_camera_access()

    # Test 2: Face detection
    if camera_ok:
        face_detection_ok = test_face_detection()
    else:
        print("⚠️  Skipping face detection test (camera not available)")
        face_detection_ok = False

    # Test 3: API endpoints
    api_ok = test_api_endpoints()

    print("\n" + "=" * 50)
    print("📊 TEST RESULTS:")
    print(f"Camera Access: {'✅ PASS' if camera_ok else '❌ FAIL'}")
    print(f"Face Detection: {'✅ PASS' if face_detection_ok else '❌ FAIL'}")
    print(f"API Endpoints: {'✅ PASS' if api_ok else '❌ FAIL'}")

    if camera_ok and face_detection_ok and api_ok:
        print("\n🎉 All tests passed! System is ready for use.")
    else:
        print("\n⚠️  Some tests failed. Check the issues above.")

if __name__ == "__main__":
    run_full_test()
