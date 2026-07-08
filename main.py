import os

from dotenv import load_dotenv
from openai import OpenAI

# Read .env file
load_dotenv()

llm_key = os.getenv("LLM_API_KEY")
llm_model = os.getenv("LLM_MODEL")
llm_base_url = os.getenv("LLM_BASE_URL")

# Initialize the OpenAI client (pointing to Grok)
client = OpenAI(
    api_key=llm_key,
    base_url=llm_base_url
)

# Hardcoded request to send to chat bot
response = client.chat.completions.create(
    model=llm_model,
    messages=[
        {"role": "user", "content": "Tell me a joke."}
    ],
    temperature=0.7
)

# reponse from Grok
print(response.choices[0].message.content)
