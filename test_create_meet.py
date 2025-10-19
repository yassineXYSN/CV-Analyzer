#!/usr/bin/env python3
"""
Test Create Meet Endpoint
This script tests the create-meet endpoint with sample data.
"""

import requests
import json

def test_create_meet():
    """Test the create-meet endpoint"""
    print("=" * 60)
    print("Testing Create Meet Endpoint")
    print("=" * 60)
    
    url = "http://localhost:8000/api/hr/interview-slots/create-meet"
    
    # Sample data
    payload = {
        "application_id": 38,
        "admin_id": 88,
        "candidate_name": "Yassine Chtourou",
        "job_title": "Développeur Full-Stack Senior",
        "company_name": "techcorp",
        "interview_date": "18/10/2025 à 22:30"
    }
    
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print("-" * 60)
    
    try:
        response = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        try:
            response_data = response.json()
            print(f"Response Data: {json.dumps(response_data, indent=2)}")
        except json.JSONDecodeError:
            print(f"Response Text: {response.text}")
        
        if response.status_code == 200:
            print("SUCCESS: Create meet request sent successfully!")
        else:
            print("ERROR: Request failed")
            
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to server")
        print("Make sure your FastAPI server is running")
    except requests.exceptions.Timeout:
        print("ERROR: Request timed out")
    except Exception as e:
        print(f"ERROR: {e}")
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)
    
    print("\nTo test manually:")
    print("1. Set N8N_WEBHOOK_URL environment variable")
    print("2. Go to the Zoom meeting setup page")
    print("3. Complete all instruction steps")
    print("4. Click 'Créer la réunion Zoom'")
    print("5. Check the server console for n8n request/response logs")

if __name__ == "__main__":
    test_create_meet()
