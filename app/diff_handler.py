import os

DEFAULT_MAX_DIFF_CHARS = 80000


def get_max_diff_chars() -> int:
    raw = os.getenv("MAX_DIFF_CHARS", str(DEFAULT_MAX_DIFF_CHARS))
    try:
        return int(raw)
    except ValueError:
        return DEFAULT_MAX_DIFF_CHARS


def read_diff_files(file: str) -> str:
    with open(file, "r", encoding="utf-8") as handle:
        return handle.read()


def validate_diff(diff_text: str) -> str:
    if not diff_text or not diff_text.strip():
        raise ValueError("Diff is empty")
    max_chars = get_max_diff_chars()
    if len(diff_text) > max_chars:
        raise ValueError(
            f"Diff exceeds max length of {max_chars} characters"
        )
    return diff_text
