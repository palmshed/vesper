# PR Bot with Gemini AI

This bot automatically analyzes pull requests using Google's Gemini AI and posts code review comments.

## Features

- Analyzes code changes in pull requests
- Provides code quality feedback
- Identifies potential issues and bugs
- Suggests improvements
- Posts detailed analysis as PR comments
- Can author code changes directly when enabled

## Setup

1. **GitHub App**
    Create a GitHub App for Vesper to post comments as a dedicated bot:
    - Use the hosted app: https://github.com/apps/vesper-review
    - If you self-host, create a GitHub App named "Vesper Review" from https://github.com/settings/apps or your organization's settings.
    - Set permissions: Repository permissions - Contents: Read, Issues: Read & Write, Pull requests: Read & Write
    - Subscribe the webhook to **Pull request**, **Issue comment**, and **Pull request review comment** events (the last one enables triggers from the Files changed tab).
    - Generate and download a private key
    - Install the app on your repository

2. **Required Secrets**
     - `GEMINI_API_KEY`: Your Google Gemini API key
     - `VESPER_APP_ID`: The App ID from the GitHub App settings
     - `VESPER_PRIVATE_KEY`: The private key content (paste the entire .pem file content)
     - `WEBHOOK_SECRET`: A secret string for webhook signature verification (used in webhook mode)

3. **GitHub App Installation (for Webhook Mode)**
    Install Vesper Review on your repository. This is required for Webhook Mode.

## How It Works

### Webhook Mode
Use this mode for new installations. It uses one hosted deployment for connected repositories.

1. Install the GitHub App on your repository
2. The hosted bot automatically receives webhooks for PR events
3. Analysis is posted directly without repository-specific setup

### Workflow Mode (Legacy)
*This mode is deprecated in favor of Webhook Mode. Support will continue for existing users, but new features and improvements will prioritize Webhook Mode.*

1. Run the setup script: `curl -fsSL https://raw.githubusercontent.com/bniladridas/vesper/main/bin/setup-vesper | bash`
    (Use `--update` to update existing, `--dry-run` to preview, `--repo URL` for custom source)
    Or manually copy `vesper/` and `.github/workflows/vesper.yml` to your repository
2. Set required secrets: `GEMINI_API_KEY`, `VESPER_APP_ID`, `VESPER_PRIVATE_KEY`
3. When a PR is opened/updated, the workflow runs and posts analysis

### CLI Mode
Run manually: `python vesper/vesper.py --repo owner/repo --pr 123`

*Note: The local webhook server uses Flask's development server, suitable for testing. For production self-hosting outside Vercel, use a WSGI server like Gunicorn.*

## Migration from Workflow Mode to Webhook Mode

Webhook Mode uses one deployment for connected repositories:

- **One deployment**: One Vercel instance handles all repositories
- **No per-repository secrets**: API keys and credentials managed in one place
- **Shared updates**: Deployments update connected repositories

### Migration Steps

1. **Deploy to Vercel**:
    - Fork this repository
    - Connect Vercel to the repository and deploy `main`
    - Set environment variables: `GEMINI_API_KEY`, `VESPER_APP_ID`, `VESPER_PRIVATE_KEY`, `WEBHOOK_SECRET`

2. **Install GitHub App**:
    - Install Vesper Review on your repositories
    - Remove repository-specific secrets and workflow files if desired

3. **Verify**:
    - Test with a new PR to ensure analysis posts correctly
    - Workflow Mode can remain as fallback during transition

## Security

- **Webhook signature verification**: All webhook requests are validated using HMAC-SHA256
- **GitHub App authentication**: Uses secure app tokens with minimal required permissions. Installation tokens are treated as opaque strings and may use GitHub's longer `ghs_` token format.
- **Environment variables**: Sensitive keys are stored securely in Vercel/env vars

## Code Authoring Features

Vesper can author code changes as a contributor to repositories:

### Auto-Commit Suggestions
- Applies code suggestions to PR branches
- Creates commits with fixes and improvements
  - In webhook mode, this is triggered by commenting `/apply` (requires `enable_authoring: true` and write/admin permissions).

### Improvement PRs
- Creates new PRs with additional improvements
- Works alongside existing PR review process

### Configuration
Set `enable_authoring: true` in `vesper/config.yaml` and configure:
- `auto_commit_suggestions`: Apply suggestions directly to PRs
- `create_improvement_prs`: Generate improvement PRs
- `improvement_branch_pattern`: Naming pattern for improvement branches

### Security Note
Authoring features require write access to repositories. Ensure proper permissions are granted to the GitHub App or token.

## Customization

Modify `vesper/config.yaml` to adjust:
- Analysis focus: 'all', 'security', 'performance', 'quality'
- Gemini model: 'gemini-3.5-flash' by default; override with `VESPER_GEMINI_MODEL`
- Temperature and token limits
- Authoring features (enable/disable auto-committing and improvement PRs)

## Troubleshooting

**Workflow Mode:**
1. Check GitHub Actions runs for the workflow
2. Verify secrets are set in repository settings
3. Ensure PR has write permissions

**Webhook Mode:**
1. Check Vercel function logs at https://vercel.com/[your-account]/[project]/functions
2. Verify GitHub webhook delivery status in repository settings > webhooks
3. Ensure environment variables are set correctly in Vercel dashboard
4. Confirm the GitHub App is installed and has repository access
5. Verify GitHub App webhook URL and secret match Vercel deployment

**Common Issues:**
- Invalid Gemini API key: Check quota and key validity
- Quota/rate-limit hits: Vesper auto-cools down per PR (env: `VESPER_QUOTA_COOLDOWN_SECONDS`, default `1800`)
- Webhook signature errors: Ensure webhook secret matches
- Permission errors: Verify GitHub App has required permissions
