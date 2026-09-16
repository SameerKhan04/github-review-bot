import json
import os

from openai import OpenAI


def get_ai_review(prompt: str) -> dict:
    llm_key = os.getenv("LLM_API_KEY")
    llm_model = os.getenv("LLM_MODEL")
    llm_base_url = os.getenv("LLM_BASE_URL")

    client = OpenAI(
        api_key=llm_key,
        base_url=llm_base_url,
    )
    response = client.chat.completions.create(
        model=llm_model,
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
    )
    llm_response = response.choices[0].message.content or ""

    cleaned_response = llm_response.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(cleaned_response)
    except json.JSONDecodeError:
        return {
            "summary": "Error: Failed to parse LLM response.",
            "bugs": [],
            "readability_issues": [],
            "security_concerns": [],
            "suggestions": [],
        }
