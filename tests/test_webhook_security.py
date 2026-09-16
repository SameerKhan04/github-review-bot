import pytest

from app.webhook_security import (
    build_signature_header,
    verify_github_signature,
)


def test_valid_signature_passes(monkeypatch):
    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", "super-secret")
    payload = b'{"ok": true}'
    header = build_signature_header(payload, "super-secret")
    verify_github_signature(payload, header)


def test_invalid_signature_raises(monkeypatch):
    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", "super-secret")
    payload = b'{"ok": true}'
    with pytest.raises(PermissionError, match="Invalid webhook signature"):
        verify_github_signature(payload, "sha256=deadbeef")


def test_missing_header_raises(monkeypatch):
    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", "super-secret")
    with pytest.raises(PermissionError, match="Missing"):
        verify_github_signature(b"{}", None)


def test_production_without_secret_raises(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("GITHUB_WEBHOOK_SECRET", raising=False)
    with pytest.raises(PermissionError, match="required in production"):
        verify_github_signature(b"{}", None)
