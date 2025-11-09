import json 
import time 
from agents.orchestrator import AgentOrchestrator


def test_all_sample_emails():
    # Load test 
    with open('data/sample_emails.json', 'r') as f:
        emails = json.load(f)
    
    orchestrator = AgentOrchestrator()
    
    print("="*80)
    print(" Testing LangGraph Orchestrator on all sample emails")
    print("="*80)

    results = []

    for i, email in enumerate(emails,1):
        print(f"\n\n{'='*80}")
        print(f"TEST {i}/{len(emails)}: {email['subject']}")
        print(f"From: {email['sender']}")
        print(f"{'='*80}")

        full_text = f"{email['subject']}\n\n{email['body']}"

        start_time = time.time()

        try:
            result = orchestrator.process_email(full_text)

            if result.get("error"): 
                raise Exception(result["error"])

            end_time = time.time()
            processing_time = end_time - start_time

            
            print(f"\n{'='*80}")
            print(f"✅ TEST {i} SUMMARY")
            print(f"{'='*80}")
            print(f"Processing Time: {processing_time:.2f}s")
           
            decision = result.get("decision")
            response = result.get("response")
            quality_check = result.get("quality_check")
            
            if decision:
                print(f"Decision: {decision.action.upper()}")
                print(f"Priority: {decision.priority}")
            if response:
                print(f"Response Length: {len(response.full_email.split())} words")
            if quality_check:
                print(f"Quality Approved: {quality_check.approved}")
                print(f"Quality Confidence: {quality_check.confidence:.2f}")

            results.append({
                "email_id": email['id'],
                "success": True, 
                "error": None,
                "processing_time": processing_time,
                "decision": decision.action if decision else None,
                "priority": decision.priority if decision else None,
                "response_length": len(response.full_email.split()) if response else 0,
                "quality_approved": quality_check.approved if quality_check else None,
                "quality_confidence": quality_check.confidence if quality_check else None,
            })

        except Exception as e:
            end_time = time.time()
            processing_time = end_time - start_time
            print(f"\n❌ TEST {i} FAILED with error: {str(e)}")
            
           
            results.append({
                "email_id": email['id'],
                "success": False,
                "error": str(e),
                "processing_time": processing_time,
                "decision": None,
                "priority": None,
                "response_length": 0,
                "quality_approved": None,
                "quality_confidence": None,
            })
            
        
        print("\nPausing for 10 seconds to respect API rate limits...")
        time.sleep(10)
    # Overall statistics
    print(f"\n\n{'='*80}")
    print(" OVERALL TEST STATISTICS")
    print("="*80)
    
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    
    print(f"\nTotal Emails Tested: {len(results)}")
    print(f"Successful: {len(successful)} ({len(successful)/len(results)*100:.1f}%)")
    print(f"Failed: {len(failed)} ({len(failed)/len(results)*100:.1f}%)")
    
    if successful:
        avg_time = sum(r["processing_time"] for r in successful) / len(successful)
        print(f"\nAverage Processing Time: {avg_time:.2f}s")
        
        # Decision breakdown
        decisions = {}
        for r in successful:
            decision = r.get("decision", "unknown")
            decisions[decision] = decisions.get(decision, 0) + 1
        
        print(f"\n Decision Breakdown:")
        for decision, count in decisions.items():
            percentage = (count / len(successful)) * 100
            print(f"   {decision}: {count} ({percentage:.1f}%)")
        
        # Response length stats
        lengths = [r["response_length"] for r in successful if r.get("response_length")]
        if lengths:
            print(f"\n Response Length Stats:")
            print(f"   Average: {sum(lengths)/len(lengths):.0f} words")
            print(f"   Min: {min(lengths)} words")
            print(f"   Max: {max(lengths)} words")
    
    # Save results
    with open('test_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n✅ Results saved to test_results.json")
    
    return results

if __name__ == "__main__":
    test_all_sample_emails()