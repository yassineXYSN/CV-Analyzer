#!/usr/bin/env python3
"""
Test Zoom Meeting Setup Page
This script tests the Zoom meeting setup page route.
"""

import requests
import sys

def test_zoom_setup_page():
    """Test the Zoom meeting setup page"""
    print("=" * 60)
    print("Testing Zoom Meeting Setup Page")
    print("=" * 60)
    
    # Test URL with sample parameters
    base_url = "http://localhost:8000"  # Adjust if your server runs on a different port
    endpoint = "/api/hr/interview-slots/zoom-meeting-setup"
    
    # Sample parameters (you'll need to use real IDs from your database)
    params = {
        "application_id": 1,  # Replace with a real application ID
        "admin_id": 1         # Replace with a real admin ID
    }
    
    url = f"{base_url}{endpoint}"
    
    print(f"Testing URL: {url}")
    print(f"Parameters: {params}")
    print("-" * 60)
    
    try:
        response = requests.get(url, params=params, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("SUCCESS: Page loaded successfully!")
            print(f"Content Length: {len(response.text)} characters")
            
            # Check if the page contains expected content
            content = response.text
            expected_elements = [
                "Configuration Zoom",
                "Instructions importantes",
                "Créer une réunion Zoom",
                "application_id",
                "admin_id"
            ]
            
            print("\nChecking for expected content:")
            for element in expected_elements:
                if element in content:
                    print(f"✓ Found: {element}")
                else:
                    print(f"✗ Missing: {element}")
                    
        elif response.status_code == 404:
            print("ERROR: Page not found - check if the route is properly registered")
        elif response.status_code == 500:
            print("ERROR: Server error - check the application and admin IDs")
            print(f"Response: {response.text}")
        else:
            print(f"ERROR: Unexpected status code: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to the server")
        print("Make sure your FastAPI server is running on http://localhost:8000")
    except requests.exceptions.Timeout:
        print("ERROR: Request timed out")
    except Exception as e:
        print(f"ERROR: {e}")
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)
    
    print("\nTo test manually:")
    print("1. Start your FastAPI server")
    print("2. Go to: http://localhost:8000/api/hr/interview-slots/zoom-meeting-setup?application_id=1&admin_id=1")
    print("3. Replace application_id and admin_id with real values from your database")

if __name__ == "__main__":
    test_zoom_setup_page()
