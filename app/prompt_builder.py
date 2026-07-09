def build_review_prompt(diff_text:str) -> str:
    prompt = f"""You are a senior software engineer performing a code review. Analyze the following code diff and respond ONLY in valid JSON matching this exact structure:

{{
    "summary": "string",
    "bugs": ["string", "string"],
    "readability_issues": ["string"],
    "security_concerns": ["string"],
    "suggestions": ["string"]
}}
Rules:
- summary must be 1-2 sentences.
- bugs must be a list of concrete logic errors or missed edge cases.
- readability_issues must be a list of naming, clarity, or structure issues.
- security_concerns must be a list of security risks.
- suggestions must be a list of actionable improvements.
- If a category has no items, return an empty list.
- Base your review only on the provided diff.
- Do not provide any explanation or extra information outside of the json format
DO NOT include any text outside the JSON object. Make sure the json isn't wrapped in markdown or any text, your exact output should be the Json format above. If a category is empty, return the header as an empty list, DO NOT disinclude it from the output.Each category should have the following:
- Summary: One or two sentences on what the diff does.
- Bugs: Logic errors, edge cases missed, etc.
- Readability: Naming, clarity, structure, etc.
- Security concerns: Injection risks, hardcoded secrets, unsafe operations, etc.
- Suggestions: General improvements.

Diff: {diff_text}
"""
    return prompt

def format_review_comment(review_dict: dict) -> str:
    """Converts the AI review dictionary into a GitHub Markdown comment."""
    
    comment = f"## AI Code Review\n\n"
    comment += f"**Summary:** {review_dict.get('summary', 'No summary provided.')}\n\n"
    
    # Format Bugs
    bugs = review_dict.get('bugs', [])
    if bugs:
        comment += "### Bugs & Edge Cases\n"
        for bug in bugs:
            comment += f"- {bug}\n"
        comment += "\n"
        
    # Format Readability
    readability = review_dict.get('readability_issues', [])
    if readability:
        comment += "### Readability\n"
        for issue in readability:
            comment += f"- {issue}\n"
        comment += "\n"
        
    # Format Security
    security = review_dict.get('security_concerns', [])
    if security:
        comment += "### Security Concerns\n"
        for concern in security:
            comment += f"- {concern}\n"
        comment += "\n"
        
    # Format Suggestions
    suggestions = review_dict.get('suggestions', [])
    if suggestions:
        comment += "### Suggestions\n"
        for suggestion in suggestions:
            comment += f"- {suggestion}\n"
            
    return comment