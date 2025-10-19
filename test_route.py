#!/usr/bin/env python3
"""
Test the Zoom Meeting Setup Route
"""

import requests

def test_route():
    """Test the zoom meeting setup route"""
    url = "http://localhost:8000/api/hr/interview-slots/zoom-meeting-setup"
    params = {
        "application_id": 38,
        "admin_id": 88
    }
    
    print(f"Testing URL: {url}")
    print(f"Parameters: {params}")
    print("-" * 50)
    
    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("SUCCESS: Page loaded successfully!")
            print(f"Content Length: {len(response.text)} characters")
            
            # Check for key content
            content = response.text
            if "Configuration Zoom" in content:
                print("✓ Found: Configuration Zoom")
            if "Instructions importantes" in content:
                print("✓ Found: Instructions importantes")
            if "Créer une réunion Zoom" in content:
                print("✓ Found: Créer une réunion Zoom")
                
        elif response.status_code == 404:
            print("ERROR: Page not found")
        elif response.status_code == 500:
            print("ERROR: Server error")
            print(f"Response: {response.text[:500]}...")
        else:
            print(f"ERROR: Unexpected status code: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to server")
        print("Make sure your FastAPI server is running")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_route()
