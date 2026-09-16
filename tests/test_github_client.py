from unittest.mock import patch

import pytest

from app.diff_handler import validate_diff
from app.github_client import get_pr_diff, post_pr_comment


def test_validate_diff_rejects_empty():
    with pytest.raises(ValueError, match="empty"):
        validate_diff("   ")


def test_validate_diff_respects_max_chars(monkeypatch):
    monkeypatch.setenv("MAX_DIFF_CHARS", "8")
    with pytest.raises(ValueError, match="max length"):
        validate_diff("123456789")


def test_validate_diff_accepts_ok_payload():
    assert validate_diff("ok diff") == "ok diff"


@patch("app.github_client.requests.get")
def test_get_pr_diff_success(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.text = "diff here"
    assert get_pr_diff("https://example.test/diff", token="abc") == "diff here"


@patch("app.github_client.requests.get")
def test_get_pr_diff_error(mock_get):
    mock_get.return_value.status_code = 404
    with pytest.raises(ValueError, match="Failed to fetch diff"):
        get_pr_diff("https://example.test/diff", token="abc")


@patch("app.github_client.requests.post")
def test_post_pr_comment_success(mock_post):
    mock_post.return_value.status_code = 201
    post_pr_comment("https://example.test/comments", "hello", token="abc")
    mock_post.assert_called_once()


@patch("app.github_client.requests.post")
def test_post_pr_comment_error(mock_post):
    mock_post.return_value.status_code = 403
    mock_post.return_value.text = "forbidden"
    with pytest.raises(ValueError, match="Failed to post comment"):
        post_pr_comment("https://example.test/comments", "hello", token="abc")
