from unittest.mock import patch

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from app.github_app_auth import (
    app_credentials_configured,
    build_app_jwt,
    clear_token_cache,
    get_github_token,
    get_installation_token,
)


def generate_pem() -> str:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )
    return pem.decode("utf-8")


@pytest.fixture
def app_credentials(monkeypatch, tmp_path):
    pem = generate_pem()
    key_path = tmp_path / "app.pem"
    key_path.write_text(pem, encoding="utf-8")
    monkeypatch.setenv("GITHUB_APP_ID", "12345")
    monkeypatch.setenv("GITHUB_APP_PRIVATE_KEY_PATH", str(key_path))
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    clear_token_cache()
    return pem


def test_app_credentials_from_path(app_credentials):
    assert app_credentials_configured()
    token = build_app_jwt()
    assert isinstance(token, str)
    assert token.count(".") == 2


def test_private_key_from_escaped_env(monkeypatch):
    pem = generate_pem()
    monkeypatch.setenv("GITHUB_APP_ID", "99")
    monkeypatch.setenv("GITHUB_APP_PRIVATE_KEY", pem.replace("\n", "\\n"))
    monkeypatch.delenv("GITHUB_APP_PRIVATE_KEY_PATH", raising=False)
    assert app_credentials_configured()
    assert build_app_jwt().count(".") == 2


def test_pat_fallback_when_app_not_configured(monkeypatch):
    monkeypatch.delenv("GITHUB_APP_ID", raising=False)
    monkeypatch.delenv("GITHUB_APP_PRIVATE_KEY", raising=False)
    monkeypatch.delenv("GITHUB_APP_PRIVATE_KEY_PATH", raising=False)
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_test")
    assert get_github_token(installation_id=7) == "ghp_test"


def test_missing_credentials_raise(monkeypatch):
    monkeypatch.delenv("GITHUB_APP_ID", raising=False)
    monkeypatch.delenv("GITHUB_APP_PRIVATE_KEY", raising=False)
    monkeypatch.delenv("GITHUB_APP_PRIVATE_KEY_PATH", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    with pytest.raises(ValueError, match="No GitHub credentials"):
        get_github_token()


@patch("app.github_app_auth.requests.post")
def test_installation_token_is_cached(mock_post, app_credentials):
    mock_post.return_value.status_code = 201
    mock_post.return_value.json.return_value = {"token": "ghs_install"}

    first = get_installation_token(42)
    second = get_installation_token(42)

    assert first == second == "ghs_install"
    assert mock_post.call_count == 1
    assert get_github_token(42) == "ghs_install"
