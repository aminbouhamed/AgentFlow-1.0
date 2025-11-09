import time
from agents.classifier import classify_email
from agents.researcher import research_company
from agents.rag_agent import RAGAgent
from agents.writer import WriterAgent
from agents.quality_checker import QualityCheckerAgent
from agents.decision_agent import DecisionAgent

def diagnose_pipeline():
    """Time each agent individually"""
    
    test_email = """Subject: AI Implementation Query

Hello, we need AI for quality control in manufacturing.

Best regards,
Geberit gmbH"""
    
    print("="*80)
    print(" PERFORMANCE DIAGNOSIS")
    print("="*80)
    
    # 1. Classifier
    print("\n1️⃣ Testing Classifier...")
    start = time.time()
    classification = classify_email(test_email)
    classifier_time = time.time() - start
    print(f"   ✅ Classifier: {classifier_time:.2f}s")
    
    # 2. Researcher 
    print("\n2️⃣ Testing Researcher...")
    start = time.time()
    research = research_company(
        classification.company_name,
        classification.key_requirements
    )
    researcher_time = time.time() - start
    print(f"   ✅ Researcher: {researcher_time:.2f}s")
    
    # 3. RAG
    print("\n3️⃣ Testing RAG...")
    start = time.time()
    rag = RAGAgent()
    rag_results = rag.retrieve(
        query=" ".join(classification.key_requirements),
        industry=research.industry,
        requirements=classification.key_requirements,
        limit=2
    )
    rag_time = time.time() - start
    print(f"   ✅ RAG: {rag_time:.2f}s")
    
    # 4. Writer
    print("\n4️⃣ Testing Writer...")
    start = time.time()
    writer = WriterAgent()
    response = writer.write_response(
        classification=classification,
        research=research,
        rag_results=rag_results,
        original_email=test_email
    )
    writer_time = time.time() - start
    print(f"   ✅ Writer: {writer_time:.2f}s")
    
    # 5. Quality Checker
    print("\n5️⃣ Testing Quality Checker...")
    start = time.time()
    checker = QualityCheckerAgent()
    quality_check = checker.check_quality(
        response=response,
        classification=classification,
        original_email=test_email
    )
    quality_time = time.time() - start
    print(f"\nResponse Subject: {response.subject}")
    print(f"Response: {response.full_email[:200]}...")
    print(f"   ✅ Quality Checker: {quality_time:.2f}s")
    
    # 6. Decision
    print("\n6️⃣ Testing Decision...")
    start = time.time()
    decision_agent = DecisionAgent()
    decision = decision_agent.make_decision(
        quality_check=quality_check,
        classification=classification
    )
    decision_time = time.time() - start
    print(f"   ✅ Decision: {decision_time:.2f}s")
    
    # Summary
    total = (classifier_time + researcher_time + rag_time + 
             writer_time + quality_time + decision_time)
    
    print(f"\n{'='*80}")
    print(f" TIMING BREAKDOWN")
    print(f"{'='*80}")
    print(f"Classifier:      {classifier_time:>6.2f}s ({classifier_time/total*100:>5.1f}%)")
    print(f"Researcher:      {researcher_time:>6.2f}s ({researcher_time/total*100:>5.1f}%)")
    print(f"RAG:             {rag_time:>6.2f}s ({rag_time/total*100:>5.1f}%)")
    print(f"Writer:          {writer_time:>6.2f}s ({writer_time/total*100:>5.1f}%)")
    print(f"Quality Checker: {quality_time:>6.2f}s ({quality_time/total*100:>5.1f}%)")
    print(f"Decision:        {decision_time:>6.2f}s ({decision_time/total*100:>5.1f}%)")
    print(f"{'='*80}")
    print(f"TOTAL:           {total:>6.2f}s")
    print(f"{'='*80}\n")
    
    # Bottleneck
    times = {
        "Classifier": classifier_time,
        "Researcher": researcher_time,
        "RAG": rag_time,
        "Writer": writer_time,
        "Quality Checker": quality_time,
        "Decision": decision_time
    }
    
    slowest = max(times, key=times.get)
    print(f"BOTTLENECK: {slowest} ({times[slowest]:.2f}s)")
    
    if times[slowest] > 10:
        print(f"⚠️  WARNING: {slowest} is extremely slow!")
        print(f"   Expected: <5s | Actual: {times[slowest]:.2f}s")

if __name__ == "__main__":
    diagnose_pipeline()