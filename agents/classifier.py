from typing import TypedDict, Literal
from pydantic import BaseModel, Field
from tools.llm_utils import get_llm


class EmailClassification(BaseModel):
    """Structured output for email classification"""

    intent: Literal["sales_inquiry", "support_request", "partnership", "other"] = Field(
        description="Primary intent of the email"
    )
    urgency: Literal["high", "medium", "low"] = Field(
        description="Urgency level of the email"
    )
    company_name: str = Field(
        description="The official legal name of the company sending the inquiry, typically found in the sender field or signature. Prioritize names like 'AutoParts GmbH' over descriptive phrases."
    )
    key_requirements: list[str] = Field(
        description="List of key requirements or questions mentioned"
    )
    confidence: float = Field(
        description="Confidence score 0.0-1.0 ",
        ge=0.0,
        le=1.0
    )

#def format_email_for_llm(email_data: dict) -> str:
#    """Formats a structured email dictionary into a clean string for the LLM."""
#    return f"""
#    SUBJECT: {email_data.get('subject', '')}
#    SENDER: {email_data.get('sender', '')}
#    
#    BODY:
#    {email_data.get('body', '')}
#    """
def classify_email(email_data: str) -> "EmailClassification":
    """
    Classify email using Bedrock LLM and extract key informations
        
    Args:
    email_text: dict with subject body and sender fields
    
    Returns:
    EmailClassification with structured data
    
    """
#    formatted_email = format_email_for_llm(email_data)
    llm = get_llm("claude-3-haiku") 

    #structured output 
    structured_llm = llm.with_structured_output(EmailClassification)

    system_prompt = """You are an expert email classifier for a business. Analyze the email, which has been formatted with SUBJECT, SENDER, and BODY tags.
    
    Analyze the email and extract:
    1. Primary intent (sales_inquiry, support_request, partnership, other)
    2. Urgency level (high, medium, low)
    3. The formal company name, often found in the sender field or email signature (e.g., ending in GmbH, AG, etc.). If no formal name is found, then use the sender's full name.
    4. key requirements/questions from the body or subject but mostly from the body.
    5. Your Confidence in this classification (0.0-1.0) 
    
    Be precise and extract only factual information."""

    response = structured_llm.invoke(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Classify this email:\n\n{email_data}"}
        ]
    )

    return response
#Test the classifier 
if __name__ == "__main__":
    test_email = """
    Subject: Partnership Inquiry - AI Solutions
    
    Hi,
    
    I'm reaching out from TechCorp GmbH. We're interested in exploring
    potential AI solutions for our customer service department. 
    
    Specifically, we need:
    - Automated email response system
    - Integration with our existing CRM
    - German language support
    
    Can we schedule a call next week?
    
    Best regards,
    Michael Schmidt
    CTO, TechCorp GmbH
    """
    result = classify_email(test_email)
    print(f"Intent: {result.intent}")
    print(f"Company: {result.company_name}")
    print(f"Urgency: {result.urgency}")
    print(f"Key Requirements: {result.key_requirements}")
    print(f"Confidence: {result.confidence}")
