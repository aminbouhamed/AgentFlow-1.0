import json 
from agents.classifier import classify_email
from agents.researcher import research_company

def test_full_pipeline(): 
    """test classifier --> researcher pipeline"""

    with open("data/sample_emails.json", "r") as f:
        emails = json.load(f)

    emails = emails[0] 
    full_text = f"{emails['subject']}\n\n{emails['body']}"   

    print("=" * 80)
    print(" TESTING FULL PIPELINE")
    print("=" * 80)

     # 1. Classify
    print("\n1 CLASSIFICATION")
    classification = classify_email(full_text)
    print(f"   Intent: {classification.intent}")
    print(f"   Company: {classification.company_name}")
    print(f"   Requirements: {classification.key_requirements}")
    print(f"   Urgency: {classification.urgency}")
    print(f"   Confidence: {classification.confidence:.2f}")    

    # 2. Research
    print("\n2 RESEARCH")
    research = research_company(
        company_name=classification.company_name,
        requirements=classification.key_requirements
    )
    print(f"   Industry: {research.industry}")
    print(f"   Size: {research.company_size}")
    print(f"   relevance: {research.relevant_experience[:150]   }...")  # Print first 150 chars
    print(f"   Key Insights: {research.key_insights[0]}...")  # Print first insight only
    print(f"   Confidence: {research.confidence:.2f}")

    print("\n FULL PIPELINE TEST COMPLETED")
    print("=" * 80)

if __name__ == "__main__":
    test_full_pipeline()