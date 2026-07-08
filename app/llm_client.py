import json
import os

from dotenv import load_dotenv
from openai import OpenAI

# Read .env file
load_dotenv()

llm_key = os.getenv("LLM_API_KEY")
llm_model = os.getenv("LLM_MODEL")
llm_base_url = os.getenv("LLM_BASE_URL")

def get_ai_review(prompt: str) -> dict:
    # 1. Initialize client
    client = OpenAI(
        api_key=llm_key,
        base_url=llm_base_url
    )
    # 2. Make the API call
    response = client.chat.completions.create(
        model=llm_model,
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    # 3. Extract the text content
    llm_response = response.choices[0].message.content
    
    # Clean out any markdown blocks the LLM might have added
    cleaned_response = llm_response.replace("```json", "").replace("```", "").strip()
    
    # 4. Parse securely with a fallback
    try:
        review_dict = json.loads(cleaned_response)
        return review_dict
    except json.JSONDecodeError:
        # If the LLM completely hallucinates and breaks the JSON, return a safe fallback dictionary
        return {
            "summary": "Error: Failed to parse LLM response.",
            "bugs": [],
            "readability_issues": [],
            "security_concerns": [],
            "suggestions": []
        }
    