from flask import Flask, request, jsonify
from app.diff_handler import validate_diff
from app.prompt_builder import build_review_prompt
from app.llm_client import get_ai_review

# Initialise the Flask application
app = Flask(__name__)

# Define the endpoint and allowed HTTP methods
@app.route('/review', methods=['POST'])
def handle_review():
    try:
        # 1. Extract the JSON payload from the incoming request
        data = request.get_json()
        
        # We expect the payload to look like: {"diff": "+ new code \n - old code"}
        if not data or 'diff' not in data:
            return jsonify({"error": "Missing 'diff' in request body"}), 400
            
        diff_text = data['diff']
        
        # 2. Validate the diff (this will raise a ValueError if it's empty or too long)
        validate_diff(diff_text)
        
        # 3. Build the prompt
        prompt = build_review_prompt(diff_text)
        
        # 4. Get the parsed review dictionary from your LLM client
        review_dict = get_ai_review(prompt)
        
        # 5. Return the successful JSON response with a 200 OK status
        return jsonify(review_dict), 200

    except ValueError as e:
        # Catch validation errors and return a 400 Bad Request
        return jsonify({"error": str(e)}), 400
        
    except Exception as e:
        # Catch unexpected errors and return a 500 Internal Server Error
        return jsonify({"error": "An internal server error occurred"}), 500