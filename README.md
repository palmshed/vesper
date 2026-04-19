# Friday Gemini AI <img src="website/assets/logo.png" align="right" width="100">

[![CI](https://github.com/bniladridas/friday_gemini_ai/actions/workflows/ci.yml/badge.svg)](https://github.com/bniladridas/friday_gemini_ai/actions/workflows/ci.yml)
[![Security](https://github.com/bniladridas/friday_gemini_ai/actions/workflows/security.yml/badge.svg)](https://github.com/bniladridas/friday_gemini_ai/actions/workflows/security.yml)
[![Dependencies](https://github.com/bniladridas/friday_gemini_ai/actions/workflows/dependencies.yml/badge.svg)](https://github.com/bniladridas/friday_gemini_ai/actions/workflows/dependencies.yml)
[![HarperBot](https://github.com/bniladridas/friday_gemini_ai/actions/workflows/harperbot.yml/badge.svg)](https://github.com/bniladridas/friday_gemini_ai/actions/workflows/harperbot.yml)

Ruby gem for integrating with Google's Gemini AI models.

The full API of this library can be found in [docs/reference/api.md](docs/reference/api.md).

# Installation

```bash
gem install friday_gemini_ai
```

Set your API key in `.env`:

```
GEMINI_API_KEY=your_api_key
```

> [!NOTE]
> Ensure your API key is kept secure and not committed to version control.

# HarperBot Integration

HarperBot provides automated PR code reviews using Google's Gemini AI. It supports two deployment modes:

### Webhook Mode (Recommended)
This is the preferred deployment path. You need to:

- Install the [`harper new line`](https://github.com/apps/harper-new-line) and grant it access to the repositories you want to monitor.
- Provision these secrets (in Vercel or another host) so the webhook server can authenticate with both Gemini and GitHub:
  - `GEMINI_API_KEY`
  - `HARPERBOT_GEMINI_API_KEY` *(optional override)*
  - `HARPER_BOT_APP_ID`
  - `HARPER_BOT_PRIVATE_KEY`
  - `WEBHOOK_SECRET`
- Subscribe the app webhooks to **Pull request**, **Issue comment**, and **Pull request review comment** (Files changed tab) events so HarperBot receives new PRs, inline review-comment triggers, and manual `/analyze` commands.
- When you migrate the app to a different GitHub account, uninstall the previous installation so the retired app stops receiving webhooks and you avoid duplicate comments.
- Regenerate the webhook secret whenever the app changes hands (or whenever you suspect it was leaked) and update the `WEBHOOK_SECRET` environment variable before resuming deployments.
- Deploy the webhook service behind a production WSGI server (for example, Gunicorn) whenever you self-host it outside Vercel; Flask's dev server is not safe for production traffic.

Once those requirements are met, the centralized HarperBot instance receives webhooks from any connected repository without per-repo secrets.

**Quick checklist before you deploy:** install the HarperBot GitHub App, configure the five secrets above, and serve the webhook process through a WSGI server when not on Vercel so you stay secure.

### Workflow Mode (Legacy)
- Repository-specific GitHub Actions workflow
- Requires secrets setup per repository
- Automated setup: `curl -fsSL https://raw.githubusercontent.com/bniladridas/friday_gemini_ai/main/bin/setup-harperbot | bash` (use `--update` to update, `--dry-run` to preview)
- **Note:** This is legacy mode for existing users. New installations should use Webhook Mode for better scalability and centralized management

For detailed setup instructions, see [harperbot/HarperBot.md](harperbot/HarperBot.md).

# Usage

### Basic Setup

**Security Note for Automated Setup:** The recommended `curl | bash` method downloads and executes code from the internet. For security, review the script at https://github.com/bniladridas/friday_gemini_ai/blob/main/bin/setup-harperbot before running. Alternatively, download first: `curl -O https://raw.githubusercontent.com/bniladridas/friday_gemini_ai/main/bin/setup-harperbot`, inspect, then `bash setup-harperbot`.

```ruby
require 'friday_gemini_ai'
GeminiAI.load_env

client = GeminiAI::Client.new               # Default: gemini-2.5-pro
fast_client = GeminiAI::Client.new(model: :flash)
```

### Model Reference

| Key           | ID                      | Use case                        |
| ------------- | ----------------------- | ------------------------------- |
| `:pro`        | `gemini-2.5-pro`        | Most capable, complex reasoning |
| `:flash`      | `gemini-2.5-flash`      | Fast, general-purpose           |
| `:flash_2_0`  | `gemini-2.0-flash`      | Legacy support                  |
| `:flash_lite` | `gemini-2.0-flash-lite` | Lightweight legacy              |

# Capabilities

Capabilities include text (content generation, summaries, documentation), chat (multi-turn Q&A and assistants), image (image-to-text analysis), and CLI (for quick prototyping and automation).

# Features

Features include multiple model support (Gemini 2.5 + 2.0 families with automatic fallback), text generation (configurable parameters, safety settings), image analysis (base64 image input, detailed descriptions), chat (context retention, system instructions), and security (API key masking, retries, and rate limits with 1s default, 3s CI).

# Handling errors

When the library is unable to connect to the API,
or if the API returns a non-success status code (i.e., 4xx or 5xx response),
a subclass of `GeminiAI::APIError` will be thrown:

```ruby
response = client.generate_text('Hello').catch do |err|
  if err.is_a?(GeminiAI::APIError)
    puts err.status  # 400
    puts err.name    # BadRequestError
    puts err.headers # {server: 'nginx', ...}
  else
    raise err
  end
end
```

Error codes are as follows:

| Status Code | Error Type                 |
| ----------- | -------------------------- |
| 400         | `BadRequestError`          |
| 401         | `AuthenticationError`     |
| 403         | `PermissionDeniedError`   |
| 404         | `NotFoundError`           |
| 422         | `UnprocessableEntityError` |
| 429         | `RateLimitError`          |
| >=500       | `InternalServerError`     |
| N/A         | `APIConnectionError`      |

### Retries

Certain errors will be automatically retried 2 times by default, with a short exponential backoff.
Connection errors (for example, due to a network connectivity problem), 408 Request Timeout, 409 Conflict,
429 Rate Limit, and >=500 Internal errors will all be retried by default.

You can use the `max_retries` option to configure or disable this:

```ruby
# Configure the default for all requests:
client = GeminiAI::Client.new(max_retries: 0)  # default is 2

# Or, configure per-request:
client.generate_text('Hello', max_retries: 5)
```

### Timeouts

Requests time out after 60 seconds by default. You can configure this with a `timeout` option:

```ruby
# Configure the default for all requests:
client = GeminiAI::Client.new(timeout: 20)  # 20 seconds (default is 60)

# Override per-request:
client.generate_text('Hello', timeout: 5)
```

On timeout, an `APIConnectionTimeoutError` is thrown.

Note that requests which time out will be [retried twice by default](#retries).

# Advanced Usage

### Logging

> [!IMPORTANT]
> All log messages are intended for debugging only. The format and content of log messages
> may change between releases.

#### Log levels

The log level can be configured via the `GEMINI_LOG_LEVEL` environment variable or client option.

Available log levels, from most to least verbose:

- `'debug'` - Show debug messages, info, warnings, and errors
- `'info'` - Show info messages, warnings, and errors
- `'warn'` - Show warnings and errors (default)
- `'error'` - Show only errors
- `'off'` - Disable all logging

```ruby
require 'friday_gemini_ai'

client = GeminiAI::Client.new(log_level: 'debug')  # Show all log messages
```

# Frequently Asked Questions

# Semantic versioning

This package generally follows [SemVer](https://semver.org/spec/v2.0.0.html) conventions, though certain backwards-incompatible changes may be released as minor versions:

1. Changes that only affect static types, without breaking runtime behavior.
2. Changes to library internals which are technically public but not intended or documented for external use. _(Please open a GitHub issue to let us know if you are relying on such internals.)_
3. Changes that we do not expect to impact the vast majority of users in practice.

We take backwards-compatibility seriously and work hard to ensure you can rely on a smooth upgrade experience.

We are keen for your feedback; please open an [issue](https://github.com/bniladridas/friday_gemini_ai/issues) with questions, bugs, or suggestions.

# Requirements

Ruby 3.0 or later is supported. The following runtimes are supported: Ruby 3.0+, JRuby (compatible versions), and TruffleRuby (compatible versions).

Note that Windows support is limited; Linux and macOS are recommended.

# Migration Guide

Gemini 1.5 models have been deprecated. Use `:pro` for `gemini-2.5-pro` or `:flash` for `gemini-2.5-flash`. Legacy options (`:flash_2_0`, `:flash_lite`) remain supported for backward compatibility.

# Environment Variables

```bash
# Required
GEMINI_API_KEY=your_api_key_here

# Optional
GEMINI_LOG_LEVEL=debug  # debug | info | warn | error
```

### CLI Shortcuts

```bash
./bin/gemini test
./bin/gemini generate "Your prompt"
./bin/gemini chat
```

# GitHub Actions Integration

Friday Gemini AI includes a built-in GitHub Actions workflow for automated PR reviews via **HarperBot**, powered by Gemini AI.

### HarperBot: Automated PR Analysis

HarperBot provides AI-driven code review and analysis directly in pull requests. Key capabilities include configurable focus (`all`, `security`, `performance`, `quality`), code quality/documentation/test coverage analysis, security and performance issue detection, inline review comments with actionable suggestions, and clean minimal structured feedback output.

Was this helpful?

### RAG (Retrieval Augmented Generation)

HarperBot includes a comprehensive RAG system that fetches current context from 90+ sources to supplement AI knowledge beyond its training cutoff (May 2024).

**Configuration:** Edit `harperbot/config.yaml`:

```yaml
# Enable RAG
enable_rag: true

# Choose sources (default shown)
rag_sources: pypi npm security github docs stackoverflow news weather reddit hackernews crates go dockerhub web_search youtube arxiv devto aws_docs azure_docs gcp_docs huggingface kaggle medium producthunt apt brew conda nuget maven pub helm terraform_registry cocoapods packagist rubygems kubernetes cloudflare vercel heroku slack discord telegram jest pytest rspec sonarcloud postgresql mongodb redis prisma swagger graphql github_actions gitlab_ci jenkins datadog newrelic sentry openai anthropic cohere digitalocean linode fastly auth0 clerk supabase cypress playwright vitest mysql elasticsearch algolia meilisearch rabbitmq kafka pulsar grpc circleci actions prometheus grafana stripe paypal braintree sendgrid mailgun ses ansible puppet packer vagrant firebase_functions langchain
```

**RAG Source Categories:**

| Category | Example Sources |
|----------|----------------|
| Package Managers | pypi, npm, crates, go, dockerhub, apt, brew, conda, nuget, maven, pub, helm, cocoapods, packagist, rubygems |
| Cloud | aws_docs, azure_docs, gcp_docs, terraform_registry, kubernetes, cloudflare, vercel, heroku, digitalocean, linode, fastly |
| Security | security, snyk, github, dependabot, sonarcloud, auth0, clerk, supabase |
| Docs/Community | docs, stackoverflow, reddit, hackernews, youtube, arxiv, devto, medium, producthunt, gitbook, confluence, slack, discord, telegram |
| Testing | jest, pytest, rspec, cypress, playwright, vitest |
| Databases | postgresql, mongodb, redis, prisma, mysql, elasticsearch, algolia, meilisearch, rabbitmq, kafka, pulsar |
| Messaging | kafka, rabbitmq, pulsar |
| API | swagger, graphql, rest, grpc |
| CI/CD | github_actions, gitlab_ci, jenkins, circleci, actions |
| Monitoring | datadog, newrelic, sentry, prometheus, grafana |
| AI/ML | openai, anthropic, cohere, huggingface, kaggle, langchain |
| Payments | stripe, paypal, braintree |
| Email | sendgrid, mailgun, ses |
| Infrastructure | ansible, puppet, packer, vagrant |

**Environment Variables for RAG:**

```bash
# Optional API keys for premium sources
NEWS_API_KEY=              # newsapi.org (tech news)
OPENWEATHER_API_KEY=       # openweathermap.org (weather)
YOUTUBE_API_KEY=          # YouTube Data API (tutorials)
SNYK_API_KEY=             # Snyk (vulnerabilities)
KAGGLE_API_KEY=           # Kaggle (datasets)
SONARCLOUD_TOKEN=          # SonarCloud (code quality)
CONFLUENCE_URL=           # Confluence (internal docs)
CONFLUENCE_API_KEY=      # Confluence API
WEATHER_LOCATION=        # Default: "San Francisco"
```

**How RAG Works:**

1. Extracts package/dependency names from changed files
2. Fetches current info from configured sources
3. Prepends "Current Context (April 2026)" section to AI prompt
4. Model receives up-to-date information about dependencies, docs, and best practices

### Workflow Highlights

* **Pull Requests:** triggered on open, update, or reopen
* **Push to main:** runs Gemini CLI verification
* **Concurrency control:** cancels redundant runs for efficiency

Required permissions:

```yaml
permissions:
  contents: read
  pull-requests: write
  issues: write
  statuses: write
```

# Local Development & Testing

```bash
bundle exec rake test          # Run tests
bundle exec rake rubocop       # Optional lint check
gem build *.gemspec            # Verify build
```

### Test Workflows Locally

Using [act](https://github.com/nektos/act):

```bash
brew install act
act -j test --container-architecture linux/amd64
```

# Examples

### Text Generation

```ruby
client = GeminiAI::Client.new
puts client.generate_text('Write a haiku about Ruby')
```

### Image Analysis

```ruby
image_data = Base64.strict_encode64(File.binread('path/to/image.jpg'))
puts client.generate_image_text(image_data, 'Describe this image')
```

### Chat

```ruby
messages = [
  { role: 'user', content: 'Hello!' },
  { role: 'model', content: 'Hi there!' },
  { role: 'user', content: 'Tell me about Ruby.' }
]
puts client.chat(messages, system_instruction: 'Be helpful and concise.')
```

# Conventional Commits

Consistent commit messages are enforced via a local Git hook.

```bash
cp scripts/commit-msg .git/hooks/
chmod +x .git/hooks/commit-msg
```

**Types:** `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `ci`
Example:

```bash
git commit -m "ci: configure vercel python build"
```

# Documentation

* [Documentation](docs/index.md)
* [Quickstart](docs/start/quickstart.md)
* [API Reference](docs/reference/api.md)
* [Cookbook](docs/reference/cookbook.md)
* [Best Practices](docs/guides/practices.md)
* [CI/CD Workflows](docs/guides/workflows.md)
* [Changelog](docs/CHANGELOG.md)
* [Contributing](docs/CONTRIBUTING.md)
* [Resources](docs/guides/resources.md)

# Contributing

Fork → Branch → Commit → Pull Request.

# License

MIT → see [LICENSE](LICENSE).

<div align="center">

[<sup>© 2026 Friday Gemini AI • Hand-crafted for Rubyists</sup>](https://bniladridas.github.io/friday_gemini_ai/)

</div>
