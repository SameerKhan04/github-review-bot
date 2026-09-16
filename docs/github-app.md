# GitHub App setup

Create a GitHub App so this bot can be installed on multiple repositories
instead of using one personal access token.

## 1. Register the App

1. GitHub → **Settings** → **Developer settings** → **GitHub Apps** → **New GitHub App**.
2. Set a unique name and homepage URL (your App Runner URL is fine).
3. **Webhook URL:** `https://<your-public-host>/review`
4. **Webhook secret:** generate a long random string and store it as
   `GITHUB_WEBHOOK_SECRET`.
5. Permissions:
   - **Metadata:** Read-only
   - **Pull requests:** Read & write (needed to post review comments)
6. Subscribe to events:
   - `Pull request`
   - `Installation` (so installs on other repos are visible in logs)
7. Where can this App be installed?
   - **Any account** if you want org teammates to install it on repos you
     develop in (an org owner still has to approve).
   - **Only on this account** if you only need your personal repos.

After creating the App, note:

- **App ID** → `GITHUB_APP_ID`
- **Generate a private key** → PEM file contents → `GITHUB_APP_PRIVATE_KEY`
  (escape newlines as `\n` if you paste into a single env var) **or** mount
  the file and set `GITHUB_APP_PRIVATE_KEY_PATH`

## 2. Install on repositories

**Your user account**

1. Open the App’s **Install** page.
2. Choose **Only select repositories** and pick the repos that should get
   automatic reviews.
3. Open a pull request. The bot should comment within a minute.

**Another repo you develop in**

- If you are an **org owner** (or the org allows members to install apps),
  install the App and select that repo.
- If you are only a **collaborator**, ask an org owner / repo admin to
  install the App on that repository (or to approve your install request).
  Write access alone cannot add GitHub Apps or org webhooks.

You do **not** add a separate repo webhook when using a GitHub App. The App’s
webhook URL receives events for every installed repo.

## 3. Environment variables

```
GITHUB_APP_ID=123456
GITHUB_APP_PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----"
GITHUB_WEBHOOK_SECRET=long-random-string
APP_ENV=production
```

Optional local-dev fallback if App credentials are omitted:

```
GITHUB_TOKEN=ghp_...
```

The PAT must be able to read diffs and create issue comments on the target
repo. Prefer the GitHub App in production so each install gets its own
short-lived token.

## 4. How auth works at runtime

1. GitHub POSTs to `/review` with `X-Hub-Signature-256` and an
   `installation.id` in the payload.
2. The bot verifies the HMAC, builds an App JWT from the private key, and
   exchanges it for an installation access token.
3. That token is used to `GET` the PR diff and `POST` the review comment.

Installation `created` / `deleted` events are acknowledged and logged. They
do not trigger a review.

## 5. Security notes

- Never commit the PEM or webhook secret.
- Production (`APP_ENV=production`) rejects webhooks when the secret is
  missing or the signature is invalid.
- Rotate the private key from the GitHub App settings if it leaks.
- The App only needs pull-request write; do not grant Contents write or
  Administration.
