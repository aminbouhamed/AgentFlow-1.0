# agents/writer.py
import time
from typing import List
from pydantic import BaseModel, Field
from tools.llm_utils import get_llm
from agents.rag_agent import RAGResults
from agents.researcher import CompanyResearch
from agents.classifier import EmailClassification


class EmailResponse(BaseModel):
    """Structured output for the final email (lightweight validation)."""
    subject: str = Field(description="Subject line of the email")
    full_email: str = Field(description="Complete email body, ~200-300 words")
    tone: str = Field(description="Tone of the message", default="professional")
    key_points_included: List[str] = Field(default_factory=list)


class WriterAgent:
    """
    Writer agent composes high-quality personalized responses using Claude 3.5 Sonnet.
    Optimized for smaller prompt context and manual parsing instead of full structured output.
    """

    def __init__(self):
       
        self.llm = get_llm("claude-3-5-sonnet", temperature=0.7)
        self.llm.model_kwargs["max_tokens"] = 500


    def write_response(
        self,
        classification: EmailClassification,
        research: CompanyResearch,
        rag_results: RAGResults,
        original_email: str
    ) -> EmailResponse:
        """
        Generate personalized email response (OPTIMIZED)
        """
        
        print(f" Writer Agent: Generating response...",flush=True)
        start_time = time.time()
        
        
        system_prompt = """You are a business development representative writing email responses.

Guidelines:
- Keep responses 200-300 words
- Be professional and helpful
- Reference relevant case studies when available
- Include clear next steps
- Write complete, ready-to-send emails"""

        case_study_mention = ""
        if rag_results.documents:
            top_doc = rag_results.documents[0]
            case_study_mention = f"Relevant experience: {top_doc.title}"
        
        
        user_prompt = f"""Write professional email response:

TO: {classification.company_name}
THEIR NEEDS: {', '.join(classification.key_requirements[:2])}
INDUSTRY: {research.industry}
{case_study_mention}

Generate complete email (subject + body, 150-200 words)."""

        try:
            structured_llm = self.llm.with_structured_output(EmailResponse)
            
            response = structured_llm.invoke([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ])
            
            elapsed = time.time() - start_time
            word_count = len(response.full_email.split())
            
            print(f"✅ Writer Agent: Complete in {elapsed:.2f}s ({word_count} words)",flush=True)
            
            
            if not response.key_points_included:
                response.key_points_included = classification.key_requirements[:2]
            
            return response

        except Exception as e:
            print(f"❌ Writer failed: {e}",flush=True)
            
            return EmailResponse(
                subject=f"Re: {classification.key_requirements[0]}",
                greeting=f"Dear {classification.company_name} team,",
                opening="Thank you for your inquiry.",
                body="We'd be happy to discuss how our AI solutions can help. Our team specializes in implementing production-ready AI systems.",
                call_to_action="Would you be available for a brief call next week?",
                closing="Best regards,\nThe Team",
                full_email="Dear team,\n\nThank you for your inquiry. We'd be happy to discuss our AI solutions.\n\nBest regards,\nThe Team",
                tone="professional",
                key_points_included=classification.key_requirements[:2]
            )


    
    

    def _format_rag_results(self, rag_results: RAGResults, max_docs: int = 2, max_chars: int = 180) -> str:
        """Compactly summarize top documents for prompt context."""
        if not rag_results.documents:
            return "No previous cases retrieved."
        snippets = []
        for i, doc in enumerate(rag_results.documents[:max_docs], 1):
            snippet = doc.content[:max_chars].replace("\n", " ")
            snippets.append(f"{i}. {doc.title}: {snippet}...")
        return "\n".join(snippets)

    def _parse_email_output(self, text: str) -> tuple[str, str]:
        """Extract subject and body from model output."""
        lines = text.splitlines()
        subject_line = "Subject: "
        subject = next((l.replace("Subject:", "").strip() for l in lines if l.lower().startswith("subject")), "Follow-up regarding your inquiry")
        body_start = text.find(subject_line)
        body = text[body_start + len(subject_line):].strip() if body_start != -1 else text.strip()
        return subject, body
