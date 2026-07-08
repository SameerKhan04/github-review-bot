import os

from dotenv import load_dotenv
from openai import OpenAI

from app.diff_handler import read_diff_files, validate_diff
from app.prompt_builder import build_review_prompt

# Read .env file
load_dotenv()

llm_key = os.getenv("LLM_API_KEY")
llm_model = os.getenv("LLM_MODEL")
llm_base_url = os.getenv("LLM_BASE_URL")

# Load and validate diff text
diff_text = read_diff_files("tests/fixtures/sample_diff.txt")
try:
    validate_diff(diff_text)
    prompt = build_review_prompt(diff_text) # Builiding review prompt (should not run if validate diff fails)
except ValueError as e:
    print(e)

# Initialize the OpenAI client (pointing to Grok)
client = OpenAI(
    api_key=llm_key,
    base_url=llm_base_url
)

# Hardcoded request to send to chat bot
response = client.chat.completions.create(
    model=llm_model,
    messages=[
        {"role": "user", "content": prompt}
    ],
    temperature=0.7
)

# reponse from Grok
print(response.choices[0].message.content)
