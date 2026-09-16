import json
import os
import sqlite3
from unittest.mock import patch

import pytest

from app.api import app
from app.database import init_db
from app.webhook_security import build_signature_header

WEBHOOK_SECRET = "test-webhook-secret"


@pytest.fixture(autouse=True)
def isolated_env(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_FILE", str(tmp_path / "reviews.db"))
    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", WEBHOOK_SECRET)
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("GITHUB_TOKEN", "test-pat")
    monkeypatch.delenv("GITHUB_APP_ID", raising=False)
    monkeypatch.delenv("GITHUB_APP_PRIVATE_KEY", raising=False)
    init_db()


@pytest.fixture
def client():
    app.config["TESTING"] = True
    return app.test_client()


def signed_headers(payload: bytes, event: str) -> dict:
    return {
        "Content-Type": "application/json",
        "X-GitHub-Event": event,
        "X-Hub-Signature-256": build_signature_header(payload, WEBHOOK_SECRET),
    }


def post_event(client, event: str, body: dict, secret: str | None = WEBHOOK_SECRET):
    payload = json.dumps(body).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "X-GitHub-Event": event,
    }
    if secret is not None:
        headers["X-Hub-Signature-256"] = build_signature_header(payload, secret)
    return client.post("/review", data=payload, headers=headers)


SAMPLE_PR_PAYLOAD = {
    "action": "opened",
    "installation": {"id": 42},
    "repository": {"full_name": "acme/demo"},
    "pull_request": {
        "number": 7,
        "diff_url": "https://api.github.com/repos/acme/demo/pulls/7.diff",
        "comments_url": "https://api.github.com/repos/acme/demo/issues/7/comments",
        "html_url": "https://github.com/acme/demo/pull/7",
    },
}

SAMPLE_REVIEW = {
    "summary": "Looks mostly good.",
    "bugs": ["Off-by-one in parser"],
    "readability_issues": [],
    "security_concerns": ["Hardcoded token"],
    "suggestions": ["Add tests"],
}


def test_health_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_ping(client):
    response = post_event(client, "ping", {"zen": "Keep it simple."})
    assert response.status_code == 200
    assert response.get_json()["status"] == "ping received successfully"


def test_unsigned_webhook_rejected_when_secret_configured(client):
    payload = json.dumps({"zen": "nope"}).encode("utf-8")
    response = client.post(
        "/review",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "X-GitHub-Event": "ping",
        },
    )
    assert response.status_code == 401


def test_invalid_signature_rejected(client):
    response = post_event(
        client, "ping", {"zen": "nope"}, secret="wrong-secret"
    )
    assert response.status_code == 401


def test_ignored_event_type(client):
    response = post_event(client, "issues", {"action": "opened"})
    assert response.status_code == 200
    assert response.get_json()["status"] == "ignored event type"


def test_ignored_pr_action(client):
    payload = {**SAMPLE_PR_PAYLOAD, "action": "closed"}
    response = post_event(client, "pull_request", payload)
    assert response.status_code == 200
    assert response.get_json()["status"] == "ignored PR action"


def test_missing_diff_url(client):
    payload = json.loads(json.dumps(SAMPLE_PR_PAYLOAD))
    payload["pull_request"].pop("diff_url")
    response = post_event(client, "pull_request", payload)
    assert response.status_code == 400
    assert "diff_url" in response.get_json()["error"]


def test_installation_created_is_logged(client):
    payload = {
        "action": "created",
        "installation": {
            "id": 99,
            "account": {"login": "acme"},
        },
        "repositories": [{"full_name": "acme/demo"}],
    }
    response = post_event(client, "installation", payload)
    assert response.status_code == 200
    body = response.get_json()
    assert body["action"] == "created"
    assert body["installation_id"] == 99


def test_installation_deleted(client):
    payload = {
        "action": "deleted",
        "installation": {"id": 99, "account": {"login": "acme"}},
        "repositories": [],
    }
    response = post_event(client, "installation", payload)
    assert response.status_code == 200
    assert response.get_json()["action"] == "deleted"


@patch("app.api.get_github_token", return_value="install-token")
@patch("app.api.get_pr_diff", return_value="diff --git a/x b/x\n+hello")
@patch("app.api.get_ai_review", return_value=SAMPLE_REVIEW)
@patch("app.api.post_pr_comment")
def test_successful_pr_review_saves_to_db(
    mock_post_comment, mock_review, mock_diff, mock_token, client
):
    response = post_event(client, "pull_request", SAMPLE_PR_PAYLOAD)
    assert response.status_code == 200
    assert response.get_json() == {"status": "success"}

    mock_token.assert_called_once_with(42)
    mock_diff.assert_called_once()
    mock_post_comment.assert_called_once()
    comment_body = mock_post_comment.call_args.args[1]
    assert "AI Code Review" in comment_body
    assert "Off-by-one" in comment_body

    conn = sqlite3.connect(os.environ["DB_FILE"])
    row = conn.execute(
        "SELECT pr_url, bug_count, security_issues_count, summary FROM pr_reviews"
    ).fetchone()
    conn.close()
    assert row == (
        "https://github.com/acme/demo/pull/7",
        1,
        1,
        "Looks mostly good.",
    )


@patch("app.api.get_github_token", return_value="install-token")
@patch("app.api.get_pr_diff", return_value="")
def test_empty_diff_returns_400(mock_diff, mock_token, client):
    response = post_event(client, "pull_request", SAMPLE_PR_PAYLOAD)
    assert response.status_code == 400
    assert "empty" in response.get_json()["error"].lower()


def test_unsigned_allowed_in_development_without_secret(client, monkeypatch):
    monkeypatch.delenv("GITHUB_WEBHOOK_SECRET")
    payload = json.dumps({"zen": "dev"}).encode("utf-8")
    response = client.post(
        "/review",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "X-GitHub-Event": "ping",
        },
    )
    assert response.status_code == 200


def test_production_requires_webhook_secret(client, monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("GITHUB_WEBHOOK_SECRET")
    payload = json.dumps({"zen": "prod"}).encode("utf-8")
    response = client.post(
        "/review",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "X-GitHub-Event": "ping",
        },
    )
    assert response.status_code == 401


def test_invalid_json_rejected(client):
    payload = b"not-json"
    response = client.post(
        "/review",
        data=payload,
        headers=signed_headers(payload, "ping"),
    )
    assert response.status_code == 400
