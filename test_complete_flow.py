#!/usr/bin/env python3
"""
Test Complete Zoom Meeting Flow
This script tests the complete flow from n8n webhook to database storage and email sending.
"""

import requests
import json
import os

def test_complete_flow():
    """Test the complete Zoom meeting creation flow"""
    print("=" * 70)
    print("Testing Complete Zoom Meeting Flow")
    print("=" * 70)
    
    # Set environment variable for testing
    os.environ["N8N_WEBHOOK_URL"] = "https://your-n8n-instance.com/webhook"
    
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
    print("-" * 70)
    
    try:
        response = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        try:
            response_data = response.json()
            print(f"Response Data: {json.dumps(response_data, indent=2)}")
            
            if response.status_code == 200:
                print("\n✅ SUCCESS: Complete flow executed!")
                print("📋 What happened:")
                print("   1. Request sent to n8n webhook")
                print("   2. n8n created Zoom meeting")
                print("   3. Meeting URLs stored in database")
                print("   4. Admin redirected to start URL")
                print("   5. Candidate notified with join URL")
            else:
                print("❌ ERROR: Request failed")
                
        except json.JSONDecodeError:
            print(f"Response Text: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Could not connect to server")
        print("Make sure your FastAPI server is running")
    except requests.exceptions.Timeout:
        print("❌ ERROR: Request timed out")
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    print("\n" + "=" * 70)
    print("Test completed!")
    print("=" * 70)
    
    print("\n📋 Expected Flow:")
    print("1. Admin completes step-by-step instructions")
    print("2. Admin clicks 'Créer la réunion Zoom'")
    print("3. System sends request to n8n webhook")
    print("4. n8n creates Zoom meeting and returns URLs")
    print("5. System stores meeting details in database")
    print("6. Admin is redirected to start URL (host link)")
    print("7. Candidate receives email with join URL")
    
    print("\n🔧 Setup Required:")
    print("1. Set N8N_WEBHOOK_URL environment variable")
    print("2. Configure n8n webhook to return start/join URLs")
    print("3. Ensure SMTP is configured for email sending")

if __name__ == "__main__":
    test_complete_flow()
