import json
import sqlite3

DB_FILE = "reviews.db"

def init_db():
    """Creates the database table if it doesn't exist."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Table to store the review metrics
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
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Metrics
    bug_count = len(review_dict.get('bugs', []))
    security_count = len(review_dict.get('security_concerns', []))
    summary = review_dict.get('summary', '')
    raw_json = json.dumps(review_dict) # Saving full payload as an insurance
    
    cursor.execute('''
        INSERT INTO pr_reviews (pr_url, summary, bug_count, security_issues_count, raw_json)
        VALUES (?, ?, ?, ?, ?)
    ''', (pr_url, summary, bug_count, security_count, raw_json))
    
    conn.commit()
    conn.close()