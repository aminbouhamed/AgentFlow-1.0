import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("\nTesting Health Endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

def test_process_email():
    """Test email processing"""
    print("\n Testing Email Processing...")
    
    test_email = {
        "email_text": """
Subject: AI Solution Inquiry

Hello,

We're a manufacturing company in Munich looking to implement AI 
for quality control. We produce automotive parts and need real-time 
defect detection. Can you help?

Best regards,
Anna Weber
AutoParts GmbH
        """,
        "priority": "high"
    }
    
    response = requests.post(
        f"{BASE_URL}/process",
        json=test_email
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✅ Success!")
        print(f"Request ID: {result['request_id']}")
        print(f"Decision: {result['decision']}")
        print(f"Confidence: {result['confidence']:.2f}")
        print(f"Processing Time: {result['processing_time']:.2f}s")
        print(f"\nGenerated Subject: {result['response_subject']}")
        print(f"\nGenerated Response (first 200 chars):")
        print(result['response_body'][:200] + "...")
    else:
        print(f"❌ Error: {response.text}")

def test_metrics():
    """Test metrics endpoint"""
    print("\n Testing Metrics Endpoint...")
    response = requests.get(f"{BASE_URL}/metrics")
    print(f"Status: {response.status_code}")
    print(f"Metrics: {json.dumps(response.json(), indent=2)}")

if __name__ == "__main__":
    print("="*80)
    print(" TESTING AGENTFLOW API")
    print("="*80)
    
    test_health()
    test_process_email()
    test_metrics()
    
    print("\n" + "="*80)
    print("✅ API Tests Complete!")
    print("="*80)
    print(f"\n View dashboard at: {BASE_URL}/metrics/dashboard")
    print(f" View API docs at: {BASE_URL}/docs")