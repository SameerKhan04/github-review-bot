#!/usr/bin/env python3
"""Send a signed sample webhook to a running review bot.

Usage (from the repo root, with the server already running):

    python scripts/send_test_webhook.py ping
    python scripts/send_test_webhook.py pr
    python scripts/send_test_webhook.py installation

Set REVIEW_BOT_URL (default http://127.0.0.1:5000/review) and
GITHUB_WEBHOOK_SECRET to match the server.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.webhook_security import build_signature_header  # noqa: E402

load_dotenv(ROOT / ".env")


EVENTS = {
    "ping": ("ping", {"zen": "Keep it logically awesome."}),
    "installation": (
        "installation",
        {
            "action": "created",
            "installation": {
                "id": 1,
                "account": {"login": "example"},
            },
            "repositories": [{"full_name": "example/demo"}],
        },
    ),
    "pr": (
        "pull_request",
        {
            "action": "opened",
            "installation": {"id": 1},
            "repository": {"full_name": "example/demo"},
            "pull_request": {
                "number": 1,
                "diff_url": "https://api.github.com/repos/example/demo/pulls/1.diff",
                "comments_url": "https://api.github.com/repos/example/demo/issues/1/comments",
                "html_url": "https://github.com/example/demo/pull/1",
            },
        },
    ),
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("event", choices=sorted(EVENTS))
    parser.add_argument(
        "--url",
        default=os.getenv("REVIEW_BOT_URL", "http://127.0.0.1:5000/review"),
    )
    args = parser.parse_args()

    github_event, body = EVENTS[args.event]
    payload = json.dumps(body).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "X-GitHub-Event": github_event,
        "User-Agent": "github-review-bot-test-script",
    }
    secret = os.getenv("GITHUB_WEBHOOK_SECRET", "")
    if secret:
        headers["X-Hub-Signature-256"] = build_signature_header(payload, secret)

    print(f"POST {args.url} event={github_event}")
    response = requests.post(args.url, data=payload, headers=headers, timeout=30)
    print(f"Status: {response.status_code}")
    print(response.text)
    return 0 if response.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
