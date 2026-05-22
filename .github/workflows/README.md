# Workflows

This directory holds the GitHub Actions workflows for the repository.

| File | Purpose |
| --- | --- |
| `ci.yml` | Runs Ruby tests and lint checks on pushes and pull requests |
| `e2e.yml` | Runs API-oriented checks when the required secret is available |
| `security.yml` | Runs dependency, code, and secret scanning |
| `dependencies.yml` | Checks dependency updates |
| `vesper.yml` | Runs Vesper on pull requests |
| `deploy-site.yml` | Publishes the static website |
| `release.yml` | Opens gem release pull requests and tags gem releases |
| `nightly.yml` | Creates daily preview releases from `main` |
| `publish-gem.yml` | Builds and publishes gem artifacts |
| `vesper-review.yml` | Publishes the Vesper Review app check |
| `manual.yml` | Provides manual release and maintenance tasks |
| `analysis.yml` | Runs repository analysis checks |
| `cleanup.yml` | Handles scheduled cleanup |
| `stale.yml` | Marks inactive issues and pull requests |
| `labeler.yml` | Applies labels from repository rules |
| `lock-merged-prs.yml` | Locks merged pull requests when configured |
| `pr-title.yml` | Checks pull request titles |
| `fix-changelog.yml` | Maintains changelog formatting |

Common secrets are `GEMINI_API_KEY`, `RUBYGEMS_API_KEY`, and `CODECOV_TOKEN`.
