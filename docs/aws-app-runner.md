# Run 24/7 on AWS App Runner

This bot is a single long-lived HTTP service. GitHub must be able to reach
`POST /review` over HTTPS whenever a pull request is opened or updated.
AWS App Runner is the simplest always-on fit: one container, public HTTPS,
secrets as environment variables.

Do **not** scale to multiple instances while using SQLite. One App Runner
instance is the supported v1 layout. Move to RDS later if you need more
than one task.

## What you need

- An AWS account and permission to use ECR + App Runner (or App Runner’s
  GitHub source integration)
- The GitHub App credentials from [github-app.md](github-app.md)
- An LLM API key

## 1. Build and push the image

From the repo root:

```bash
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REPO_NAME=github-review-bot

aws ecr create-repository --repository-name "$REPO_NAME" --region "$AWS_REGION" || true
aws ecr get-login-password --region "$AWS_REGION" \
  | docker login --username AWS --password-stdin "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

docker build -t "$REPO_NAME" .
docker tag "$REPO_NAME:latest" \
  "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${REPO_NAME}:latest"
docker push \
  "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${REPO_NAME}:latest"
```

Alternatively, create an App Runner service from this GitHub repository and
let AWS build the Dockerfile.

## 2. Store secrets

Put these in AWS Secrets Manager or SSM Parameter Store (SecureString), then
map them into the App Runner service as environment variables. Do not bake
them into the image (`.dockerignore` already excludes `.env`).

| Variable | Required | Notes |
|----------|----------|--------|
| `APP_ENV` | yes | `production` |
| `LLM_API_KEY` | yes | Provider secret |
| `LLM_MODEL` | yes | Model id |
| `LLM_BASE_URL` | yes | e.g. `https://api.openai.com/v1` or xAI |
| `GITHUB_APP_ID` | yes | Numeric App ID |
| `GITHUB_APP_PRIVATE_KEY` | yes | PEM; use `\n` for newlines |
| `GITHUB_WEBHOOK_SECRET` | yes | Same secret as the GitHub App |
| `LOG_LEVEL` | no | default `INFO` |
| `DB_FILE` | no | default `reviews.db` |
| `MAX_DIFF_CHARS` | no | default `80000` |

`GITHUB_TOKEN` is not needed when the GitHub App is configured.

## 3. Create the App Runner service

Console or CLI, using these settings:

- **Image:** the ECR URI from step 1
- **Port:** `5000`
- **Health check:** HTTP `GET /health` (path `/health`)
- **Instance size:** 0.25 vCPU / 0.5 GB is enough for v1
- **Auto scaling:** min **1**, max **1** (SQLite)
- **Timeout:** the image already uses gunicorn `--timeout 120` for LLM calls
- **Environment:** inject the secrets above

Example CLI sketch (fill the image URI and secret ARNs):

```bash
aws apprunner create-service \
  --service-name github-review-bot \
  --source-configuration '{
    "ImageRepository": {
      "ImageIdentifier": "<account>.dkr.ecr.us-east-1.amazonaws.com/github-review-bot:latest",
      "ImageRepositoryType": "ECR",
      "ImageConfiguration": {
        "Port": "5000",
        "RuntimeEnvironmentVariables": {
          "APP_ENV": "production"
        }
      }
    },
    "AutoDeploymentsEnabled": false
  }' \
  --instance-configuration '{
    "Cpu": "256",
    "Memory": "512"
  }' \
  --health-check-configuration '{
    "Protocol": "HTTP",
    "Path": "/health",
    "Interval": 10,
    "Timeout": 5,
    "HealthyThreshold": 1,
    "UnhealthyThreshold": 5
  }'
```

Prefer wiring secrets through App Runner’s connection to Secrets Manager
rather than putting PEM material in `--source-configuration` JSON.

## 4. Point GitHub at the service

Copy the App Runner default URL, for example
`https://xxxxx.awsapprunner.com`.

In the GitHub App settings:

- Webhook URL = `https://xxxxx.awsapprunner.com/review`
- Webhook secret = the same value as `GITHUB_WEBHOOK_SECRET`

Save, then open **Advanced** → **Ping**. The service should log
`Received GitHub ping` and return 200.

## 5. Verify end to end

1. Install the App on a test repository.
2. Open a small pull request.
3. Confirm an **AI Code Review** comment appears on the PR.
4. Optional: exec is not available on App Runner; metrics live in the
   container’s `reviews.db` until you add RDS. Logs will show
   `Posted review for repo=...`.

## Cost and limits

- App Runner idle/always-on compute is the small part of the bill.
- **LLM token usage** is the main ongoing cost.
- GitHub retries webhooks if the LLM call exceeds GitHub’s delivery window.
  Keep diffs within `MAX_DIFF_CHARS`. A background worker is a later
  improvement, not required for small PRs.

## When to move off this layout

- Need more than one instance, durable metrics, or multi-AZ: switch SQLite
  to RDS Postgres.
- Huge PRs / slow models: accept the webhook with 202 and run the LLM in a
  queue worker (SQS + ECS).
- Stricter networking: put ECS Fargate behind an ALB and restrict ingress
  if you add GitHub’s webhook IP ranges.

None of that is required to run 24/7.
