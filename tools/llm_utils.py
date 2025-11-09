import os 
from langchain_aws import ChatBedrock
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
load_dotenv()

os.environ['LANGCHAIN_TRACING_V2'] = 'true'
os.environ['LANGCHAIN_ENDPOINT'] = 'https://api.smith.langchain.com'

def get_llm(model: str = "claude-3-5-sonnet", temperature: float = 0.0):
    """get LLM instance with langsmith

    Args:
        model:"claude-3-5-sonnet" (smart) or "claude-3-haiku" (fast/cheap) "
        temperature: 0.0-1.0 
    """

    if model.startswith("claude-") or model.startswith("llama-"):
        # Handle Bedrock models
        print(f"Initializing Bedrock model: {model}")
        model_ids = {
            "claude-3-5-sonnet": "anthropic.claude-3-5-sonnet-20240620-v1:0",
            "claude-3-haiku": "anthropic.claude-3-haiku-20240307-v1:0",
            "llama-3-8b": "meta.llama3-8b-instruct-v1:0",
            "llama-3-70b": "meta.llama3-70b-instruct-v1:0"
        }
        return ChatBedrock(
            model_id=model_ids[model],
            region_name=os.getenv("AWS_REGION", "us-east-1"),
            model_kwargs={"temperature": temperature, "max_tokens": 3000}
        )
        
    elif model.startswith("gemini-"):
        # Handle Google Gemini models
        print(f"Initializing Google Gemini model: {model}")
        return ChatGoogleGenerativeAI(
            model=model,
            temperature=temperature,
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )
    else:
        raise ValueError(f"Unknown model provider for model: {model}")

def invoke_llm (system_prompt: str, user_message: str, model: str = "claude-3-5-sonnet"):
    """invoke LLM with system and user prompt

    Args:
        system_prompt: system prompt
        user_prompt: user prompt
        model:"claude-3-5-sonnet" (smart) or "claude-3-haiku" (fast/cheap) "
        temperature: 0.0-1.0 
    """
    llm = get_llm(model=model)
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message)
    ]
    response = llm(messages)
    return response.content