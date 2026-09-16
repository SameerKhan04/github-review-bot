import hashlib
import hmac
import logging
import os

logger = logging.getLogger(__name__)


def get_webhook_secret() -> str:
    return os.getenv("GITHUB_WEBHOOK_SECRET", "").strip()


def is_production() -> bool:
    return os.getenv("APP_ENV", "development").strip().lower() == "production"


def verify_github_signature(payload: bytes, signature_header: str | None) -> None:
    """
    Validate X-Hub-Signature-256.

    Production requires a configured secret and a valid signature.
    Development skips verification when no secret is set so local testing works.
    """
    secret = get_webhook_secret()

    if not secret:
        if is_production():
            raise PermissionError("GITHUB_WEBHOOK_SECRET is required in production")
        logger.warning(
            "GITHUB_WEBHOOK_SECRET is unset; skipping webhook signature verification"
        )
        return

    if not signature_header:
        raise PermissionError("Missing X-Hub-Signature-256 header")

    try:
        algorithm, received_signature = signature_header.split("=", 1)
    except ValueError as exc:
        raise PermissionError("Malformed X-Hub-Signature-256 header") from exc

    if algorithm != "sha256":
        raise PermissionError("Unsupported webhook signature algorithm")

    expected = hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected, received_signature):
        raise PermissionError("Invalid webhook signature")


def build_signature_header(payload: bytes, secret: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    return f"sha256={digest}"
