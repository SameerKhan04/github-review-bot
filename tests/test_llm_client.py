from types import SimpleNamespace
from unittest.mock import patch

from app.llm_client import get_ai_review


def _completion(content: str):
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
    )


@patch("app.llm_client.OpenAI")
def test_parses_json(mock_openai):
    mock_openai.return_value.chat.completions.create.return_value = _completion(
        '{"summary": "ok", "bugs": [], "readability_issues": [], '
        '"security_concerns": [], "suggestions": []}'
    )
    review = get_ai_review("prompt")
    assert review["summary"] == "ok"


@patch("app.llm_client.OpenAI")
def test_strips_markdown_fence(mock_openai):
    mock_openai.return_value.chat.completions.create.return_value = _completion(
        '```json\n{"summary": "fenced", "bugs": []}\n```'
    )
    review = get_ai_review("prompt")
    assert review["summary"] == "fenced"


@patch("app.llm_client.OpenAI")
def test_invalid_json_fallback(mock_openai):
    mock_openai.return_value.chat.completions.create.return_value = _completion(
        "this is not json"
    )
    review = get_ai_review("prompt")
    assert review["summary"].startswith("Error:")
    assert review["bugs"] == []
