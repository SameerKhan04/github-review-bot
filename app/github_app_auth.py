import logging
import os
import time

import jwt
import requests

logger = logging.getLogger(__name__)

GITHUB_API_URL = os.getenv("GITHUB_API_URL", "https://api.github.com")
USER_AGENT = "github-review-bot"
TOKEN_REFRESH_SKEW_SECONDS = 60

# installation_id -> (token, expires_at_epoch)
_token_cache: dict[int, tuple[str, float]] = {}


def load_private_key() -> str:
    """Load the GitHub App PEM key from a file path or env var."""
    path = os.getenv("GITHUB_APP_PRIVATE_KEY_PATH")
    if path:
        with open(path, encoding="utf-8") as key_file:
            return key_file.read()

    key = os.getenv("GITHUB_APP_PRIVATE_KEY", "")
    if not key:
        return ""
    return key.replace("\\n", "\n")


def app_credentials_configured() -> bool:
    return bool(os.getenv("GITHUB_APP_ID") and load_private_key())


def build_app_jwt() -> str:
    app_id = os.getenv("GITHUB_APP_ID")
    private_key = load_private_key()
    if not app_id or not private_key:
        raise ValueError("GITHUB_APP_ID and a private key are required")

    now = int(time.time())
    payload = {
        "iat": now - 60,
        "exp": now + 600,
        "iss": app_id,
    }
    return jwt.encode(payload, private_key, algorithm="RS256")


def get_installation_token(installation_id: int) -> str:
    """Mint (or reuse a cached) installation access token."""
    cached = _token_cache.get(installation_id)
    now = time.time()
    if cached and cached[1] > now + TOKEN_REFRESH_SKEW_SECONDS:
        return cached[0]

    jwt_token = build_app_jwt()
    url = f"{GITHUB_API_URL}/app/installations/{installation_id}/access_tokens"
    response = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {jwt_token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": USER_AGENT,
            "X-GitHub-Api-Version": "2022-11-28",
        },
        timeout=30,
    )
    if response.status_code != 201:
        raise ValueError(
            f"Failed to create installation token: {response.status_code}"
        )

    data = response.json()
    token = data["token"]
    expires_at = now + 3600 - TOKEN_REFRESH_SKEW_SECONDS
    _token_cache[installation_id] = (token, expires_at)
    logger.info("Issued installation token for installation_id=%s", installation_id)
    return token


def clear_token_cache() -> None:
    _token_cache.clear()


def get_github_token(installation_id: int | None = None) -> str:
    """
    Prefer a GitHub App installation token when App credentials and an
    installation id are present. Fall back to GITHUB_TOKEN for local dev.
    """
    if installation_id and app_credentials_configured():
        return get_installation_token(installation_id)

    pat = os.getenv("GITHUB_TOKEN")
    if pat:
        if installation_id and not app_credentials_configured():
            logger.info(
                "Using GITHUB_TOKEN fallback (GitHub App credentials not configured)"
            )
        return pat

    if installation_id:
        raise ValueError(
            "GitHub App credentials are not configured and GITHUB_TOKEN is unset"
        )
    raise ValueError(
        "No GitHub credentials configured. Set GitHub App env vars or GITHUB_TOKEN"
    )
