from tavily import TavilyClient
import os
from typing import List, Dict 
from dotenv import load_dotenv
load_dotenv()

client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

def search_web(query: str, max_results: int = 3) -> List[Dict]:
    """
    Search the web using Tavily

    Args:
        query (str): Search Query 
        num_results (int, optional): Number of results to return. Defaults to 5.

    Returns:
        List[Dict]: List of search results with title, url, and content.
    """
    try: 
        response = client.search(
            query=query,
            max_results=max_results,
            search_depth="basic", #or advanced for more detailed search
            include_answers=True,
            include_raw_content=False
        )

        return {
            "answer": response.get("answer", ""),
            "results": response.get("results", [])
        }
    except Exception as e:
        print(f"Error during web search: {e}")
        return {
            "answer": "",
            "results": []
        }

def search_company_info(company_name: str) -> Dict:
    """
    Search for company information using Tavily

    Args:
        company_name (str): Name of the company to search for.

    Returns:
        Dict: structured company information.
    """

    query = f"{company_name} company information industry products services"
    results = search_web(query, max_results=3) # limit to top 3 results for company info

    return {
        "company": company_name,
        "summary": results["answer"],
        "sources": [
            {
            "title": r["title"],
            "url": r["url"],
            "snippet": r["content"][:200]  # first 200 chars
            } 
        for r in results["results"]
        ]
    }


#Test 
if __name__ == "__main__":
    result = search_company_info("Siemens AG")
    print(f"Summary: {result['summary']}")
    print(f"\nSources:{len(result['sources'])} ")
