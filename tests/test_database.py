import os
import sqlite3

from app.database import init_db, save_review
from app.prompt_builder import format_review_comment


def test_save_review_persists_metrics(tmp_path, monkeypatch):
    db_path = tmp_path / "reviews.db"
    monkeypatch.setenv("DB_FILE", str(db_path))
    init_db()
    save_review(
        "https://github.com/acme/demo/pull/1",
        {
            "summary": "nits",
            "bugs": ["a", "b"],
            "security_concerns": ["xss"],
        },
    )
    conn = sqlite3.connect(os.environ["DB_FILE"])
    row = conn.execute(
        "SELECT bug_count, security_issues_count, summary FROM pr_reviews"
    ).fetchone()
    conn.close()
    assert row == (2, 1, "nits")


def test_format_review_comment_includes_sections():
    markdown = format_review_comment(
        {
            "summary": "Small change",
            "bugs": ["crash on empty input"],
            "readability_issues": ["rename foo"],
            "security_concerns": [],
            "suggestions": ["add tests"],
        }
    )
    assert "## AI Code Review" in markdown
    assert "crash on empty input" in markdown
    assert "rename foo" in markdown
    assert "add tests" in markdown
    assert "Security Concerns" not in markdown
