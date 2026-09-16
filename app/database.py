import json
import os
import sqlite3

DEFAULT_DB_FILE = "reviews.db"


def get_db_file() -> str:
    return os.getenv("DB_FILE", DEFAULT_DB_FILE)


def init_db():
    """Creates the database table if it doesn't exist."""
    conn = sqlite3.connect(get_db_file())
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pr_reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pr_url TEXT NOT NULL,
            summary TEXT,
            bug_count INTEGER,
            security_issues_count INTEGER,
            raw_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()


def save_review(pr_url: str, review_dict: dict):
    """Saves the review metadata to the SQLite database."""
    conn = sqlite3.connect(get_db_file())
    cursor = conn.cursor()

    bug_count = len(review_dict.get('bugs', []))
    security_count = len(review_dict.get('security_concerns', []))
    summary = review_dict.get('summary', '')
    raw_json = json.dumps(review_dict)

    cursor.execute('''
        INSERT INTO pr_reviews (pr_url, summary, bug_count, security_issues_count, raw_json)
        VALUES (?, ?, ?, ?, ?)
    ''', (pr_url, summary, bug_count, security_count, raw_json))

    conn.commit()
    conn.close()
