from typing import Literal
from pydantic import BaseModel, Field
from agents.quality_checker import QualityCheck
from agents.classifier import EmailClassification

class Decision(BaseModel):
    """Decision on how to handle the response"""
    action: Literal["auto_send", "human_review", "manual_handle"] = Field(
        description="What action to take with this response"
    )
    reasoning: str = Field(
        description="Detailed explanation of why this decision was made"
    )
    priority: Literal["low", "medium", "high"] = Field(
        description="Priority level for human review"
    )
    estimated_human_time: str = Field(
        description="Estimated time for human to review (e.g., '2 minutes')"
    )
    confidence_breakdown: dict = Field(
        description="Breakdown of factors affecting decision"
    )

class DecisionAgent:
    """Agent responsible for deciding what to do with generated response"""
    
    def __init__(self):
        # Decision thresholds
        self.auto_send_threshold = 0.90
        self.human_review_threshold = 0.75
    
    def make_decision(
        self,
        quality_check: QualityCheck,
        classification: EmailClassification
    ) -> Decision:
        """
        Decide what to do with the response
        
        Args:
            quality_check: Quality check results
            classification: Original email classification
            
        Returns:
            Decision with action and reasoning
        """
        
        print(f" Decision Agent: Evaluating...")
        
        # overall confidence
        confidence_factors = {
            "quality_confidence": quality_check.confidence,
            "classification_confidence": classification.confidence,
            "no_critical_issues": 1.0 if not self._has_critical_issues(quality_check) else 0.0,
            "all_requirements_met": 1.0 if len(quality_check.requirements_missed) == 0 else 0.5
        }
        
        # Weighted average
        overall_confidence = (
            confidence_factors["quality_confidence"] * 0.4 +
            confidence_factors["classification_confidence"] * 0.2 +
            confidence_factors["no_critical_issues"] * 0.2 +
            confidence_factors["all_requirements_met"] * 0.2
        )
        
        # Adjust for urgency
        urgency_factor = self._get_urgency_factor(classification.urgency)
        adjusted_confidence = overall_confidence * urgency_factor
        
        # Make decision
        if adjusted_confidence >= self.auto_send_threshold and quality_check.approved:
            action = "auto_send"
            priority = "low"
            estimated_time = "0 minutes"
            reasoning = self._build_reasoning(
                action, overall_confidence, quality_check, classification
            )
        
        elif adjusted_confidence >= self.human_review_threshold:
            action = "human_review"
            priority = self._determine_priority(classification, quality_check)
            estimated_time = "2-3 minutes"
            reasoning = self._build_reasoning(
                action, overall_confidence, quality_check, classification
            )
        
        else:
            action = "manual_handle"
            priority = "high"
            estimated_time = "10-15 minutes"
            reasoning = self._build_reasoning(
                action, overall_confidence, quality_check, classification
            )
        
        decision = Decision(
            action=action,
            reasoning=reasoning,
            priority=priority,
            estimated_human_time=estimated_time,
            confidence_breakdown=confidence_factors
        )
        
        # Log decision
        print(f" Decision: {action.upper()} (confidence: {overall_confidence:.2f})")
        print(f"   Priority: {priority}")
        print(f"   Reasoning: {reasoning[:100]}...")
        
        return decision
    
    def _has_critical_issues(self, quality_check: QualityCheck) -> bool:
        """Check if there are any critical (high severity) issues"""
        return any(
            issue.severity == "high" 
            for issue in quality_check.issues_found
        )
    
    def _get_urgency_factor(self, urgency: str) -> float:
        """Adjust confidence threshold based on urgency"""
        urgency_map = {
            "high": 0.95,    # More cautious for urgent emails
            "medium": 1.0,   # Standard
            "low": 1.05      # More lenient for low urgency
        }
        return urgency_map.get(urgency, 1.0)
    
    def _determine_priority(
        self,
        classification: EmailClassification,
        quality_check: QualityCheck
    ) -> Literal["low", "medium", "high"]:
        """Determine priority for human review"""
        
        # High priority in case of urgent emails or significant issues
        if classification.urgency == "high":
            return "high"
        
        if quality_check.issues_found:
            # severity of issues
            severities = [issue.severity for issue in quality_check.issues_found]
            if "high" in severities:
                return "high"
            elif "medium" in severities:
                return "medium"
        
        return "low"
    
    def _build_reasoning(
        self,
        action: str,
        confidence: float,
        quality_check: QualityCheck,
        classification: EmailClassification
    ) -> str:
        """Build human-readable reasoning for decision"""
        
        if action == "auto_send":
            return (
                f"High confidence ({confidence:.2f}) response with no critical issues. "
                f"All requirements addressed. Quality check passed. "
                f"Intent: {classification.intent}, Urgency: {classification.urgency}. "
                f"Safe to send automatically."
            )
        
        elif action == "human_review":
            issues = quality_check.issues_found
            issue_summary = f"{len(issues)} minor issues found" if issues else "no issues"
            
            return (
                f"Moderate confidence ({confidence:.2f}). Response quality is good but "
                f"should be reviewed by human. {issue_summary}. "
                f"Intent: {classification.intent}, Urgency: {classification.urgency}. "
                f"Quick review recommended before sending."
            )
        
        else:  # manual_handle
            return (
                f"Low confidence ({confidence:.2f}) or critical issues found. "
                f"Quality checker found: {len(quality_check.issues_found)} issues. "
                f"Requirements missed: {len(quality_check.requirements_missed)}. "
                f"Intent: {classification.intent}, Urgency: {classification.urgency}. "
                f"Requires manual handling by experienced team member."
            )

# Test function
if __name__ == "__main__":
    from agents.classifier import classify_email
    from agents.researcher import research_company
    from agents.rag_agent import RAGAgent
    from agents.writer import WriterAgent
    from agents.quality_checker import QualityCheckerAgent
    import json
    
    print("="*80)
    print(" Testing Decision Agent (Full Pipeline)")
    print("="*80)
    
    # Load test 
    with open('data/sample_emails.json', 'r') as f:
        emails = json.load(f)
    
    test_email = emails[1]
    full_text = f"{test_email['subject']}\n\n{test_email['body']}"
    
    # Run complete pipeline
    print("\n Original Email:")
    print(f"Subject: {test_email['subject']}")
    print(f"From: {test_email['sender']}")
    
    print("\n" + "="*80)
    print(" RUNNING COMPLETE AGENT PIPELINE")
    print("="*80)
    
    print("\n1. CLASSIFIER AGENT")
    classification = classify_email(test_email)
    print(f"   Intent: {classification.intent}")
    print(f"   Company: {classification.company_name}")
    print(f"   Confidence: {classification.confidence:.2f}")
    
    print("\n2. RESEARCHER AGENT")
    research = research_company(
        classification.company_name,
        classification.key_requirements
    )
    print(f"   Industry: {research.industry}")
    print(f"   Confidence: {research.confidence:.2f}")
    
    print("\n3. RAG AGENT")
    rag = RAGAgent()
    rag_results = rag.retrieve(
        query=" ".join(classification.key_requirements),
        industry=research.industry,
        requirements=classification.key_requirements,
        limit=2
    )
    print(f"   Retrieved: {len(rag_results.documents)} documents")
    print(f"   Strategy: {rag_results.retrieval_strategy}")
    
    print("\n4. WRITER AGENT")
    writer = WriterAgent()
    response = writer.write_response(
        classification=classification,
        research=research,
        rag_results=rag_results,
        original_email=full_text
    )

    print(f"   Generated: {len(response.full_email.split())} words")
    print(f"   Subject: {response.subject}")
    print(f"   Preview: {response.full_email}...")
    
    print("\n5. QUALITY CHECKER AGENT")
    checker = QualityCheckerAgent()
    quality_check = checker.check_quality(
        response=response,
        classification=classification,
        original_email=full_text
    )
    print(f"   Approved: {quality_check.approved}")
    print(f"   Confidence: {quality_check.confidence:.2f}")
    print(f"   Issues: {len(quality_check.issues_found)}")
    
    print("\n6. DECISION AGENT")
    decision_agent = DecisionAgent()
    decision = decision_agent.make_decision(
        quality_check=quality_check,
        classification=classification
    )
    
    print("\n" + "="*80)
    print(" FINAL DECISION")
    print("="*80)
    print(f"\nAction: {decision.action.upper()}")
    print(f"Priority: {decision.priority.upper()}")
    print(f"Estimated Human Time: {decision.estimated_human_time}")
    
    print(f"\n Confidence Breakdown:")
    for factor, score in decision.confidence_breakdown.items():
        print(f"   • {factor}: {score:.2f}")
    
    print(f"\n Reasoning:")
    print(f"   {decision.reasoning}")
    
    print("\n" + "="*80)
    print(" PIPELINE TEST COMPLETE")
    print("="*80)