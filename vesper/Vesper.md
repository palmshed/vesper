# PR Bot with Gemini AI

This bot automatically analyzes pull requests using Google's Gemini AI and posts code review comments.

## Features

- Analyzes code changes in pull requests
- Provides code quality feedback
- Identifies potential issues and bugs
- Suggests improvements
- Posts detailed analysis as PR comments
- Optional retrieval context is available but disabled by default.
- Authoring can apply suggestions when enabled.

## Setup

1. **GitHub App**
   Create a GitHub App for Vesper to post comments as a dedicated bot:
   - Use the hosted app: https://github.com/apps/vesper-review
   - If you self-host, create a GitHub App named "Vesper Review" from https://github.com/settings/apps or your organization's settings.
   - Set permissions: Repository permissions - Contents: Read, Issues: Read & Write, Pull requests: Read & Write
   - Generate and download a private key
   - Install the app on your repository

2. **Required Secrets**
    - `GEMINI_API_KEY`: Your Google Gemini API key (global default)
    - `VESPER_GEMINI_API_KEY`: Optional per-repo override key for Vesper
    - `VESPER_APP_ID`: The App ID from the GitHub App settings
    - `VESPER_PRIVATE_KEY`: The private key content (paste the entire .pem file content)
    - `WEBHOOK_SECRET`: A secret string for webhook signature verification (used in webhook mode)

3. **GitHub App Installation (for Webhook Mode)**
   Install Vesper Review on your repository. This is required for Webhook Mode.

## How It Works

### Webhook Mode
Use this mode for new installations. It uses one hosted deployment for connected repositories.

Before deploying, make sure you:

- Install Vesper Review and grant it access to the repositories whose PRs you want analyzed.
- Set the required environment secrets (`GEMINI_API_KEY`, `VESPER_GEMINI_API_KEY` optional, `VESPER_APP_ID`, `VESPER_PRIVATE_KEY`, and `WEBHOOK_SECRET`) in your hosting platform (Vercel, Gunicorn host, etc.) so the webhook server can authenticate with Gemini and GitHub.
- When you self-host the webhook service outside Vercel, run the Flask app behind a production-grade WSGI server such as Gunicorn; the development server is not designed for production traffic.
- Treat GitHub App installation tokens as opaque strings. GitHub may issue longer `ghs_` tokens, including JWT-shaped values, and Vesper does not depend on token length or structure.

### Workflow Mode (Legacy)
*This mode is deprecated in favor of Webhook Mode. Support will continue for existing users, but new features and improvements will prioritize Webhook Mode.*

1. Run the setup script: `curl -fsSL https://raw.githubusercontent.com/bniladridas/vesper/main/bin/setup-vesper | bash`
   (Use `--update` to update existing, `--dry-run` to preview, `--repo URL` for custom source)
   Or manually copy `vesper/` and `.github/workflows/vesper.yml` to your repository
2. Set required secrets: `GEMINI_API_KEY`, `VESPER_APP_ID`, `VESPER_PRIVATE_KEY`
3. When a PR is opened/reopened, the workflow runs and posts analysis

### Manual Analysis Trigger
Comment `/analyze` on a PR to request a fresh analysis on demand.

### Manual Apply Command
Comment `/apply` on a PR to apply Vesper suggestions as commits (requires `enable_authoring: true` and write/admin permissions).

### Manual Merge Commands
Comment one of the following on a PR to merge via Vesper (requires write/admin permissions):
- `/merge`
- `/squash`
- `/rebase`

### Help & Notices
- Comment `/help` to see Vesper capabilities.
- Vesper posts **Notice** comments when something unusual happens (no files, empty diff, missing analysis output, permission issues, not mergeable, merge failures).

### CLI Mode
Run manually: `python vesper/vesper.py --repo owner/repo --pr 123`

*Note: The local webhook server uses Flask's development server, suitable for testing. For production self-hosting outside Vercel, use a WSGI server like Gunicorn.*

## Retrieval Context

Vesper can fetch a small amount of package, security, GitHub, or documentation context before review. It is disabled by default to keep reviews fast and predictable.

### Enable

Edit `vesper/config.yaml`:

```yaml
enable_rag: true
rag_sources: [pypi, npm, rubygems, security, github, docs]
```

### Optional Keys

```bash
# Optional API keys for premium sources
NEWS_API_KEY=              # newsapi.org (tech news)
OPENWEATHER_API_KEY=       # openweathermap.org (weather)
YOUTUBE_API_KEY=          # YouTube Data API (tutorials)
SNYK_API_KEY=             # Snyk (vulnerabilities)
KAGGLE_API_KEY=           # Kaggle (datasets)
SONARCLOUD_TOKEN=        # SonarCloud (code quality)
CONFLUENCE_URL=          # Confluence (internal docs)
CONFLUENCE_API_KEY=       # Confluence API
WEATHER_LOCATION=        # Default: "San Francisco"
```

### How It Works

1. **Extract dependencies** from changed files (Python, Node.js, Rust, Go, Docker, etc.)
2. **Fetch current context** from configured sources (latest versions, docs, security advisories, tutorials)
3. **Prepend context** to AI prompt with a current timestamp
4. **Model receives** current information about dependencies, docs, and related resources

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
    - While configuring the app, subscribe to the **Pull request**, **Issue comment**, and **Pull request review comment** webhook events so Vesper sees new PRs, inline review-comment triggers, and `/analyze`/`/apply`/merge commands.
    - If you’re migrating the app between accounts, uninstall the previous installation (Settings → Installed GitHub Apps → Configure → Uninstall) so the retired app no longer receives webhooks or posts comments.

3. **Verify**:
   - Test with a new PR to ensure analysis posts correctly
   - Workflow Mode can remain as fallback during transition

## Security

- **Webhook signature verification**: All webhook requests are validated using HMAC-SHA256
- **GitHub App authentication**: Uses secure app tokens with minimal required permissions
- **Environment variables**: Sensitive keys are stored securely in Vercel/env vars

## Code Authoring Features

Vesper can now author code changes directly as a contributor to repositories:

### Auto-Commit Suggestions
- Automatically applies code suggestions to PR branches
- Creates commits with fixes and improvements
- Reduces manual work for developers

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
- Webhook signature errors: Ensure webhook secret matches
- Permission errors: Verify GitHub App has required permissions
