def read_diff_files(file: str) -> str:
    with open(file, "r") as f:
        diff_text = f.read()
    
    return diff_text

def validate_diff(diff_text: str) -> str:
    if not diff_text or not diff_text.strip():
        raise ValueError("Diff is empty")
    if len(diff_text) > 5000: # To ensure not too many tokens are being used on the free model
        raise ValueError("Diff exceeds max length")
    return diff_text