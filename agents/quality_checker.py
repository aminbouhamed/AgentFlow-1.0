from typing import List, Dict, Optional
from pydantic import BaseModel, Field, field_validator
from tools.llm_utils import get_llm
from agents.writer import EmailResponse
from agents.classifier import EmailClassification

class QualityIssue(BaseModel):
    """Single quality issue found"""
    severity: str = Field(description="low/medium/high")
    issue: str = Field(description="Description of the issue")
    suggestion: str = Field(description="How to fix it")

class QualityCheck(BaseModel):
    """Quality check results"""
    approved: bool = Field(description="Whether response passes quality check")
    confidence: float = Field(
        description="Confidence in the response quality (0-1)",
        ge=0.0,
        le=1.0
    )
    issues_found: List[QualityIssue] = Field(
        default_factory=list,
        description="List of issues found (empty list if none)"
    )
    strengths: List[str] = Field(
        default_factory=list,
        description="What the response does well"
    )
    overall_assessment: str = Field(description="Brief overall quality assessment")
    requirements_addressed: List[str] = Field(
        default_factory=list,
        description="Which requirements from original email were addressed"
    )
    requirements_missed: List[str] = Field(
        default_factory=list,
        description="Which requirements were not addressed (empty list if all addressed)"
    )
    
    
    @field_validator('issues_found', mode='before')
    @classmethod
    def validate_issues(cls, v):
        if v is None or v == "None" or v == "null":
            return []
        if isinstance(v, str):
            return []
        return v
    
    @field_validator('strengths', 'requirements_addressed', 'requirements_missed', mode='before')
    @classmethod
    def validate_lists(cls, v):
        if v is None or v == "None" or v == "null":
            return []
        if isinstance(v, str):
            
            if ',' in v:
                return [item.strip() for item in v.split(',')]
            return [v] if v else []
        return v

class QualityCheckerAgent:
    """Agent responsible for validating response quality"""
    
    def __init__(self):
        self.llm = get_llm("claude-3-haiku", temperature=0.0)
    
    def check_quality(
        self,
        response: EmailResponse,
        classification: EmailClassification,
        original_email: str
    ) -> QualityCheck:
        """
        Validate response quality
        
        Args:
            response: Generated email response
            classification: Original email classification
            original_email: Original email text
            
        Returns:
            QualityCheck with validation results
        """
        
        print(f" Quality Checker: Validating response...")
        
        system_prompt = """You are a quality assurance specialist reviewing email responses.

Your job is to check:
1. All customer requirements are addressed
2. Tone is appropriate (professional, helpful)
3. No factual errors or unsupported claims
4. Clear call-to-action is included
5. Email is concise (under 400 words)
6. Grammar and spelling are correct
7. Response is personalized (not generic)

Quality standards:
- HIGH confidence (>0.85): Ready to send, minor or no issues
- MEDIUM confidence (0.70-0.85): Needs minor revisions
- LOW confidence (<0.70): Needs significant revisions

IMPORTANT OUTPUT FORMAT RULES:
- issues_found: Return empty list [] if no issues, NOT "None" or null
- strengths: Return list of strings, minimum 2 items
- requirements_addressed: Return list of requirement strings that were addressed
- requirements_missed: Return empty list [] if all requirements met, NOT "None"
- All lists must be actual lists, never strings or null values

Be thorough but fair."""

        # Get requirements as a numbered list for clarity
        requirements_list = "\n".join([
            f"{i+1}. {req}" 
            for i, req in enumerate(classification.key_requirements)
        ])

        user_message = f"""Review this email response:

ORIGINAL EMAIL:
{original_email}

CUSTOMER REQUIREMENTS (check each one):
{requirements_list}

GENERATED RESPONSE:
Subject: {response.subject}

{response.full_email}

Provide your quality assessment:

1. approved: true or false
2. confidence: decimal between 0.0 and 1.0
3. issues_found: list of issues (use empty list [] if none found)
4. strengths: list of at least 2 positive aspects
5. overall_assessment: brief summary
6. requirements_addressed: list each requirement number that WAS addressed
7. requirements_missed: list each requirement number that was NOT addressed (use empty list [] if all were addressed)

Example of correct format:
{{
  "approved": true,
  "confidence": 0.88,
  "issues_found": [],
  "strengths": ["Clear and professional tone", "All requirements addressed"],
  "overall_assessment": "High quality response ready to send",
  "requirements_addressed": ["AI for quality control", "Defect detection", "Real-time processing"],
  "requirements_missed": []
}}

Now evaluate the response above."""

        try:
            
            structured_llm = self.llm.with_structured_output(QualityCheck)
            
            result = structured_llm.invoke([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ])
            
            
            if not isinstance(result.issues_found, list):
                result.issues_found = []
            if not isinstance(result.strengths, list):
                result.strengths = ["Response generated"]
            if not isinstance(result.requirements_addressed, list):
                result.requirements_addressed = []
            if not isinstance(result.requirements_missed, list):
                result.requirements_missed = []
            
            
            status = "✅ APPROVED" if result.approved else "⚠️ NEEDS REVISION"
            print(f"{status} (confidence: {result.confidence:.2f})")
            
            if result.issues_found:
                print(f"   Issues found: {len(result.issues_found)}")
                for issue in result.issues_found:
                    print(f"   - [{issue.severity.upper()}] {issue.issue}")
            
            return result
            
        except Exception as e:
            print(f"❌ Quality check failed: {e}")
            print(f"   Falling back to basic quality check...")
            
            
            return self._fallback_quality_check(response, classification)
    
    def _fallback_quality_check(
        self,
        response: EmailResponse,
        classification: EmailClassification
    ) -> QualityCheck:
        """
        Fallback quality check if LLM fails
        Uses simple rule-based validation
        """
        
        issues = []
        strengths = []
        
        
        word_count = len(response.full_email.split())
        if word_count > 500:
            issues.append(QualityIssue(
                severity="medium",
                issue="Response is too long (>500 words)",
                suggestion="Condense the content to be more concise"
            ))
        elif word_count < 50:
            issues.append(QualityIssue(
                severity="high",
                issue="Response is too short (<50 words)",
                suggestion="Provide more detail and context"
            ))
        else:
            strengths.append("Appropriate length")
        
        
        if not response.subject:
            issues.append(QualityIssue(
                severity="high",
                issue="Missing email subject",
                suggestion="Add a clear subject line"
            ))
        else:
            strengths.append("Has clear subject line")
        
        
        requirements_addressed = []
        requirements_missed = []
        
        response_lower = response.full_email.lower()
        for req in classification.key_requirements:
            
            req_keywords = req.lower().split()
            if any(keyword in response_lower for keyword in req_keywords if len(keyword) > 3):
                requirements_addressed.append(req)
            else:
                requirements_missed.append(req)
        
        if requirements_missed:
            issues.append(QualityIssue(
                severity="high",
                issue=f"Missing requirements: {', '.join(requirements_missed[:2])}",
                suggestion="Address all customer requirements explicitly"
            ))
        else:
            strengths.append("All requirements addressed")
        
        high_severity_count = sum(1 for i in issues if i.severity == "high")
        medium_severity_count = sum(1 for i in issues if i.severity == "medium")
        
        if high_severity_count > 0:
            confidence = 0.5
            approved = False
        elif medium_severity_count > 1:
            confidence = 0.7
            approved = False
        elif medium_severity_count == 1:
            confidence = 0.8
            approved = True
        else:
            confidence = 0.9
            approved = True
        
        if not strengths:
            strengths = ["Response generated successfully"]
        
        return QualityCheck(
            approved=approved,
            confidence=confidence,
            issues_found=issues,
            strengths=strengths,
            overall_assessment=f"Fallback quality check: {'Approved' if approved else 'Needs revision'}. {len(issues)} issues found.",
            requirements_addressed=requirements_addressed,
            requirements_missed=requirements_missed
        )

# Test function
if __name__ == "__main__":
    from agents.classifier import classify_email
    from agents.researcher import research_company
    from agents.rag_agent import RAGAgent
    from agents.writer import WriterAgent
    import json
    
    print("="*80)
    print(" Testing Quality Checker Agent")
    print("="*80)
    
    # Load test email
    with open('data/sample_emails.json', 'r') as f:
        emails = json.load(f)
    
    test_email = emails[0]
    full_text = f"{test_email['subject']}\n\n{test_email['body']}"
    
    
    print("\n1️⃣ Classifying...")
    classification = classify_email(full_text)
    
    print("\n2️⃣ Researching...")
    research = research_company(
        classification.company_name,
        classification.key_requirements
    )
    
    print("\n3️⃣ RAG retrieval...")
    rag = RAGAgent()
    rag_results = rag.retrieve(
        query=" ".join(classification.key_requirements),
        industry=research.industry,
        requirements=classification.key_requirements,
        limit=2
    )
    
    print("\n4️⃣ Writing response...")
    writer = WriterAgent()
    response = writer.write_response(
        classification=classification,
        research=research,
        rag_results=rag_results,
        original_email=full_text
    )
    
    print("\n5️⃣ Quality check...")
    checker = QualityCheckerAgent()
    quality_check = checker.check_quality(
        response=response,
        classification=classification,
        original_email=full_text
    )
    
    print("\n" + "="*80)
    print("QUALITY CHECK RESULTS")
    print("="*80)
    print(f"\nApproved: {quality_check.approved}")
    print(f"Confidence: {quality_check.confidence:.2f}")
    print(f"\nOverall Assessment:\n{quality_check.overall_assessment}")
    
    print(f"\n✅ Strengths:")
    for strength in quality_check.strengths:
        print(f"   • {strength}")
    
    if quality_check.issues_found:
        print(f"\n Issues Found:")
        for issue in quality_check.issues_found:
            print(f"   • [{issue.severity.upper()}] {issue.issue}")
            print(f"     → {issue.suggestion}")
    
    print(f"\n Requirements Check:")
    if quality_check.requirements_addressed:
        print(f"   Addressed: {', '.join(quality_check.requirements_addressed)}")
    if quality_check.requirements_missed:
        print(f"   Missed: {', '.join(quality_check.requirements_missed)}")
    else:
        print(f"   All requirements addressed ✅")