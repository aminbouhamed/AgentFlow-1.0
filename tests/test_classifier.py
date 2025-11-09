import json 
from agents.classifier import classify_email

def test_all_samples():
    """test all email samples"""
    
    with open("data/sample_emails.json", "r") as f:
        emails = json.load(f)
    
    print("testing classifier on sample Data \n")
    print("=" * 80)

    for email in emails:
        print(f"\n Email {email['id']}: {email['subject']}")
        print(f"From: {email['sender']}")

        
        result = classify_email(f"{email['subject']}\n\n{email['body']}")

        print(f"\n✅ Classification:")
        print(f"   Intent: {result.intent}")
        print(f"   Urgency: {result.urgency}")
        print(f"   Company: {result.company_name}")
        print(f"   Confidence: {result.confidence:.2f}")
        print(f"   Requirements: {result.key_requirements[:2]}")  # First 2
        print("-" * 80)

if __name__ == "__main__":
    test_all_samples()