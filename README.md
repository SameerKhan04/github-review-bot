# GitHub Review Bot

An LLM-powered GitHub App that reviews pull request diffs and posts structured
feedback as a Markdown comment. It is a long-running HTTP service: GitHub sends
webhooks, the bot fetches the diff, asks an OpenAI-compatible model for JSON
review notes, comments on the PR, and stores metrics in SQLite.

It is designed to run 24/7 (Docker locally, or AWS App Runner in production)
and can be installed on any repository a GitHub admin grants it, including
other repos you develop in.

## Overview

When a pull request is opened, updated, or reopened:

1. GitHub sends a `pull_request` webhook to `POST /review`.
2. The bot verifies `X-Hub-Signature-256`.
3. It mints a GitHub App installation token (or uses `GITHUB_TOKEN` for local dev).
4. It fetches the PR diff, validates size, and asks the LLM for JSON:
   summary, bugs, readability issues, security concerns, suggestions.
5. It posts a Markdown comment on the PR and records metrics in SQLite.

## Tech Stack

- Python 3.11, Flask, gunicorn
- OpenAI Python SDK (any OpenAI-compatible API, including xAI/Grok)
- GitHub App authentication (JWT → installation token) with PAT fallback
- SQLite (`reviews.db`) for review metrics
- Docker image for local and AWS deploys

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env
```

Fill in `.env` (never commit it):

- `LLM_API_KEY`, `LLM_MODEL`, `LLM_BASE_URL`
- GitHub App values from [docs/github-app.md](docs/github-app.md), **or**
  `GITHUB_TOKEN` for single-repo local testing
- `GITHUB_WEBHOOK_SECRET` (required when `APP_ENV=production`)

Run locally:

```bash
python main.py
```

The API listens on `http://127.0.0.1:5000`. Use a tunnel (ngrok, Cloudflare
Tunnel, etc.) if you want GitHub to reach your laptop.

```bash
pytest
```

## Docker

```bash
docker build -t github-review-bot .
docker run --rm -p 5000:5000 --env-file .env github-review-bot
```

The container runs **one gunicorn worker** because SQLite is not safe across
multiple processes. Health check: `GET /health`.

## API Usage

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/health` | Liveness/readiness for AWS |
| `POST` | `/review` | GitHub webhook receiver |

Webhook events handled:

- `ping` — App/webhook setup check
- `installation` — logs created/deleted installs (needed for other repos)
- `pull_request` — reviews `opened`, `synchronize`, and `reopened`

In production, unsigned or badly signed requests are rejected (`401`).

Diffs larger than `MAX_DIFF_CHARS` (default 80,000) are rejected so LLM
cost stays bounded.

## Connecting other repositories

The webhook handler is not locked to one repo. After you create the GitHub
App, install it on any account or organization that grants access:

- **Your own repos:** install the App and select repositories.
- **Orgs you own, or that allow member installs:** install or request install
  on selected repos.
- **Repos you only develop in:** collaborator/write access is **not** enough
  to install an App. An org owner or repo admin must install it (or approve
  your request). Once installed, the bot comments on PRs without you needing
  admin rights day to day.

See [docs/github-app.md](docs/github-app.md).

## AWS 24/7

Yes — this is a public HTTPS webhook service and should stay online. The
simplest AWS path is **App Runner** with a single instance, secrets injected
as environment variables, and the GitHub App webhook pointed at
`https://<service>/review`.

See [docs/aws-app-runner.md](docs/aws-app-runner.md).

## Project Structure

```
app/
  api.py                 Flask routes (/health, /review)
  github_client.py       Fetch diffs and post PR comments
  github_app_auth.py     GitHub App JWT + installation tokens
  webhook_security.py    HMAC signature verification
  llm_client.py          OpenAI-compatible review call
  prompt_builder.py      JSON prompt + Markdown formatter
  diff_handler.py        Empty / oversized diff checks
  database.py            SQLite metrics
main.py                  gunicorn/Flask entrypoint
Dockerfile
docs/github-app.md
docs/aws-app-runner.md
tests/
```
