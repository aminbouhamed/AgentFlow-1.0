import boto3
import json 
from botocore.config import Config
from dotenv import load_dotenv
import os
load_dotenv()


def test_bedrock():
    """test bedrock connection"""

    bedrock=boto3.client(
        service_name="bedrock-runtime",
        region_name="eu-central-1",
        config=Config(read_timeout=300)
    )

    #test claude 3.5 sonnet
    prompt="reply with connection successful if you receive"

    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 100,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    })

    try: 
        response = bedrock.invoke_model(
            modelId='anthropic.claude-3-5-sonnet-20240620-v1:0',
            body=body,
        )
        response_body = json.loads(response["body"].read())
        print("bedrock connected successfully")
        print(f"Response: {response_body['content'][0]['text']}")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False
if __name__ == "__main__":
    test_bedrock()
