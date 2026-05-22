# Workflows

This repository uses GitHub Actions for tests, security checks, release tasks, site deployment, and Vesper.

| Workflow | File | Purpose |
| --- | --- | --- |
| CI | `.github/workflows/ci.yml` | Runs tests and lint checks on pushes and pull requests |
| E2E | `.github/workflows/e2e.yml` | Runs API-oriented checks when configured |
| Security | `.github/workflows/security.yml` | Runs dependency and secret scans |
| Dependencies | `.github/workflows/dependencies.yml` | Checks dependency updates |
| Vesper | `.github/workflows/vesper.yml` | Reviews pull requests with Gemini-backed analysis |
| Site | `.github/workflows/deploy-site.yml` | Publishes the static website |
| Release | `.github/workflows/release.yml` | Handles release automation |
| Publish Gem | `.github/workflows/publish-gem.yml` | Builds and publishes package artifacts |

## Local Checks

Run the same core checks locally before opening a pull request:

```bash
bundle exec ruby test/runner.rb
bundle exec rubocop
gem build friday_gemini_ai.gemspec
```

## Secrets

Common workflow secrets are:

| Secret | Used for |
| --- | --- |
| `GEMINI_API_KEY` | Gemini API tests and Vesper |
| `RUBYGEMS_API_KEY` | RubyGems publishing |
| `CODECOV_TOKEN` | Coverage upload |

Vesper may also require GitHub App credentials when running in app mode. See [`Vesper`](../reference/vesper.md).
