import json

from flask import Flask, jsonify, request

from app.diff_handler import validate_diff
from app.github_client import get_pr_diff, post_pr_comment
from app.llm_client import get_ai_review
from app.prompt_builder import build_review_prompt, format_review_comment

# Initialise the Flask application
app = Flask(__name__)

# Define the endpoint and allowed HTTP methods
@app.route('/review', methods=['POST'])
def handle_review():
    try:
        # Identify the GitHub event type
        event_type = request.headers.get('X-GitHub-Event')
        data = request.get_json()

        # Handle the initial GitHub ping
        if event_type == 'ping':
            return jsonify({"status": "ping received successfully"}), 200

        # We only care about Pull Request events
        if event_type != 'pull_request':
            return jsonify({"status": "ignored event type"}), 200

        # We only want to review when a PR is OPENED or SYNCHRONIZED (updated)
        action = data.get('action')
        if action not in ['opened', 'synchronize', 'reopened']:
            return jsonify({"status": "ignored PR action"}), 200
        
        # Get the URL for the diff from the payload
        pr_data = data.get('pull_request', {})
        diff_url = pr_data.get('diff_url')
        
        if not diff_url:
            return jsonify({"error": "No diff_url found"}), 400

        # Fetch the actual diff text from GitHub
        diff_text = get_pr_diff(diff_url)
        
        # Validate it
        validate_diff(diff_text)
        
        # Build prompt and get AI review
        prompt = build_review_prompt(diff_text)
        review_dict = get_ai_review(prompt)
        
        # Format the review into Markdown
        comment_body = format_review_comment(review_dict)
        
        # Extract the comments URL from the webhook payload
        comments_url = pr_data.get('comments_url')
        if not comments_url:
            return jsonify({"error": "No comments_url found"}), 400
            
        # Post to Github
        post_pr_comment(comments_url, comment_body)
        
        print("SUCCESS! Posted review to GitHub.")
        return jsonify({"status": "success"}), 200

    except ValueError as e:
        # Catch validation errors and return a 400 Bad Request
        return jsonify({"error": str(e)}), 400
        
    except Exception as e:
        # Catch unexpected errors and return a 500 Internal Server Error
        return jsonify({"error": "An internal server error occurred"}), 500