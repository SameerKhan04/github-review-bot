import os

import requests


def get_pr_diff(diff_url: str) -> str:
    token = os.getenv("GITHUB_TOKEN")
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3.diff" # This tells GitHub we want the raw diff text
    }
    
    response = requests.get(diff_url, headers=headers)
    
    if response.status_code != 200:
        raise ValueError(f"Failed to fetch diff from GitHub: {response.status_code}")
        
    return response.text

def post_pr_comment(comments_url: str, comment_body: str):
    """Posts a Markdown comment to the GitHub PR."""
    token = os.getenv("GITHUB_TOKEN")
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    payload = {
        "body": comment_body
    }
    
    response = requests.post(comments_url, headers=headers, json=payload)
    
    if response.status_code != 201: # 201 means "Created"
        raise ValueError(f"Failed to post comment: {response.status_code} - {response.text}")