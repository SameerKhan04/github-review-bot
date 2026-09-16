import json
import logging

from flask import Flask, jsonify, request

import app.logging_setup  # noqa: F401
from app.database import init_db, save_review
from app.diff_handler import validate_diff
from app.github_app_auth import get_github_token
from app.github_client import get_pr_diff, post_pr_comment
from app.llm_client import get_ai_review
from app.prompt_builder import build_review_prompt, format_review_comment
from app.webhook_security import verify_github_signature

logger = logging.getLogger(__name__)

app = Flask(__name__)

REVIEWABLE_PR_ACTIONS = {"opened", "synchronize", "reopened"}


@app.route("/health", methods=["GET"])
def health():
    try:
        init_db()
    except Exception:
        logger.exception("Health check could not initialize the database")
        return jsonify({"status": "error"}), 503
    return jsonify({"status": "ok"}), 200


@app.route("/review", methods=["POST"])
def handle_review():
    raw_body = request.get_data() or b""

    try:
        verify_github_signature(
            raw_body, request.headers.get("X-Hub-Signature-256")
        )
    except PermissionError as exc:
        logger.warning("Rejected webhook: %s", exc)
        return jsonify({"error": str(exc)}), 401

    try:
        data = json.loads(raw_body.decode("utf-8") or "{}") if raw_body else {}
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON payload"}), 400

    if not isinstance(data, dict):
        return jsonify({"error": "JSON payload must be an object"}), 400

    event_type = request.headers.get("X-GitHub-Event")

    try:
        if event_type == "ping":
            logger.info("Received GitHub ping")
            return jsonify({"status": "ping received successfully"}), 200

        if event_type == "installation":
            return _handle_installation_event(data)

        if event_type != "pull_request":
            logger.info("Ignoring GitHub event type=%s", event_type)
            return jsonify({"status": "ignored event type"}), 200

        return _handle_pull_request_event(data)

    except ValueError as exc:
        logger.warning("Review request rejected: %s", exc)
        return jsonify({"error": str(exc)}), 400
    except Exception:
        logger.exception("Unhandled error processing webhook")
        return jsonify({"error": "An internal server error occurred"}), 500


def _handle_installation_event(data: dict):
    action = data.get("action")
    installation = data.get("installation") or {}
    installation_id = installation.get("id")
    account = (installation.get("account") or {}).get("login")
    repositories = [
        repo.get("full_name")
        for repo in data.get("repositories") or []
        if repo.get("full_name")
    ]
    logger.info(
        "GitHub App installation event action=%s installation_id=%s account=%s repos=%s",
        action,
        installation_id,
        account,
        repositories,
    )
    return jsonify({
        "status": "installation event recorded",
        "action": action,
        "installation_id": installation_id,
    }), 200


def _handle_pull_request_event(data: dict):
    action = data.get("action")
    if action not in REVIEWABLE_PR_ACTIONS:
        logger.info("Ignoring pull_request action=%s", action)
        return jsonify({"status": "ignored PR action"}), 200

    pr_data = data.get("pull_request") or {}
    repo = data.get("repository") or {}
    installation_id = (data.get("installation") or {}).get("id")
    repo_full_name = repo.get("full_name")
    pr_number = pr_data.get("number")

    logger.info(
        "Reviewing pull request repo=%s number=%s action=%s installation_id=%s",
        repo_full_name,
        pr_number,
        action,
        installation_id,
    )

    diff_url = pr_data.get("diff_url")
    if not diff_url:
        return jsonify({"error": "No diff_url found"}), 400

    comments_url = pr_data.get("comments_url")
    if not comments_url:
        return jsonify({"error": "No comments_url found"}), 400

    token = get_github_token(installation_id)
    diff_text = get_pr_diff(diff_url, token=token)
    validate_diff(diff_text)

    prompt = build_review_prompt(diff_text)
    review_dict = get_ai_review(prompt)
    comment_body = format_review_comment(review_dict)

    post_pr_comment(comments_url, comment_body, token=token)

    pr_html_url = pr_data.get("html_url") or ""
    save_review(pr_html_url, review_dict)

    logger.info(
        "Posted review for repo=%s number=%s",
        repo_full_name,
        pr_number,
    )
    return jsonify({"status": "success"}), 200
