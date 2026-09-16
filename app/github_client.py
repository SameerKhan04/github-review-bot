import logging
import os

import requests

logger = logging.getLogger(__name__)

USER_AGENT = "github-review-bot"
REQUEST_TIMEOUT_SECONDS = 30


def _headers(token: str, accept: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": accept,
        "User-Agent": USER_AGENT,
    }


def _require_token(token: str | None) -> str:
    if token:
        return token
    fallback = os.getenv("GITHUB_TOKEN")
    if fallback:
        return fallback
    raise ValueError(
        "No GitHub credentials available. Configure GitHub App installation "
        "tokens or set GITHUB_TOKEN for local development."
    )


def get_pr_diff(diff_url: str, token: str | None = None) -> str:
    """Fetch the raw unified diff for a pull request."""
    auth_token = _require_token(token)
    response = requests.get(
        diff_url,
        headers=_headers(auth_token, "application/vnd.github.v3.diff"),
        timeout=REQUEST_TIMEOUT_SECONDS,
    )

    if response.status_code != 200:
        raise ValueError(
            f"Failed to fetch diff from GitHub: {response.status_code}"
        )

    return response.text


def post_pr_comment(
    comments_url: str, comment_body: str, token: str | None = None
) -> None:
    """Post a Markdown comment on a GitHub pull request."""
    auth_token = _require_token(token)
    response = requests.post(
        comments_url,
        headers=_headers(auth_token, "application/vnd.github.v3+json"),
        json={"body": comment_body},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )

    if response.status_code != 201:
        raise ValueError(
            f"Failed to post comment: {response.status_code} - {response.text}"
        )
