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