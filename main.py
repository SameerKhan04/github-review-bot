import os

from dotenv import load_dotenv
from openai import OpenAI

from app.diff_handler import read_diff_files, validate_diff
from app.llm_client import get_ai_review
from app.prompt_builder import build_review_prompt

# 1. Validate diff text
diff_text = read_diff_files("tests/fixtures/sample_diff.txt")
validate_diff(diff_text)

# 2. Build prompt
prompt = build_review_prompt(diff_text)

# 3. Get review (this is your new function)
review_dict = get_ai_review(prompt)

# 4. Prove it's a dictionary by printing a specific key
print("Summary:", review_dict["summary"])
print("Bugs found:", len(review_dict["bugs"]))
if len(review_dict["bugs"]) > 0:
    print("Bugs found:", review_dict["bugs"])
if len(review_dict["readability_issues"]) > 0:
    print("Readability issues:", review_dict["readability_issues"])
if len(review_dict["security_concerns"]) > 0:
    print("Security concerns:", review_dict["security_concerns"])
print("Suggestions:", review_dict["suggestions"])
