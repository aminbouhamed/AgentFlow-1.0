from typing import Dict, List 
from pydantic import BaseModel, Field
from tools.web_search import search_company_info
from tools.llm_utils import invoke_llm

class CompanyResearch(BaseModel):
    """Structured output for company research"""

    company_name: str
    industry: str
    products_services: List[str]
    company_size: str = Field(description="e.g., 'Large entreprise', 'SME', 'Startup'")
    relevant_experience: str = Field(
        description="How our services might be relevant to them"
    )
    key_insights: List[str] = Field(
        description="Important facts to mention in response"
    )
    confidence: float 

def research_company(company_name: str, requirements: List[str]) -> CompanyResearch:
    """
    Research company using web search and Determine relevance

    Args:
        company_name: Name of the company to research
        requirements: their stated requirements/questions 
    Returns:
        CompanyResearch with structured insights
    """
    
    # web search
    search_results = search_company_info(company_name)

    # analyze with LLM
    system_prompt = """You are a business intelligence analyst.

    Given company information and their requirements, extract:
    1. Industry and main products/services
    2. Company size (large/medium/small)
    3. How our AI solutions could be relevant
    4. Key insights to personalize our response
    
    Be factual and cite the sources provided."""

    user_message = f"""Company:{company_name}

Web Search Results:
{search_results['summary']}

Sources:
{chr(10).join([f"- {s['title']}: {s['snippet']}" for s in search_results['sources']])}

Their Requirements:
{chr(10).join([f"- {r}" for r in requirements])}

Analyze this company and provide structured insights."""
    
    #  analysis with claude
    from tools.llm_utils import get_llm
    llm = get_llm("claude-3-5-sonnet")
    structured_llm = llm.with_structured_output(CompanyResearch)

    response = structured_llm.invoke([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ])

    print(f"Research complete! Confidence: {response.confidence}",flush=True)
    return response



#Test
if __name__ == "__main__":
    result = research_company(
        company_name="AutoParts GmbH",
        requirements=[
            "AI for quality control",
            "Defect detection",
            "Real-time processing"
        ]
    )
    print(f"\nIndustry: {result.industry}")
    print(f"Products: {result.products_services}")
    print(f"Relevance: {result.relevant_experience}")
    print(f"Insights: {result.key_insights}")