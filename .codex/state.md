# Codex State

<br>

Memory version: `2026.05.26.4`
Updated: `2026-05-26`

<br>

Keep this file short. Store facts that must survive into the next session.

<br>

# Project

<br>

This repo publishes the `friday_gemini_ai` gem. Runtime code is required with `vesper`. The GitHub App is `Vesper Review`.

<br>

Gem releases use tags like `friday_gemini_ai/v1.7.1`. The app deploys from `main`; app behavior is commit-based, not gem-tag based.

<br>

# Runtime

<br>

Ruby support is `>= 3.3`. `.ruby-version` is `3.3.11`. CI tests Ruby `3.3` and `3.4`. Do not lower the gemspec floor for EOL Ruby versions.

<br>

Gemini calls use `https://generativelanguage.googleapis.com/v1beta/models`. Vesper defaults to `gemini-3.5-flash`; hosted runs can override with `VESPER_GEMINI_MODEL`.

<br>

Main Ruby aliases are `:pro -> gemini-pro-latest`, `:flash -> gemini-3.5-flash`, `:flash_lite -> gemini-3.1-flash-lite`, `:pro_2_5 -> gemini-2.5-pro`, and `:flash_2_5 -> gemini-2.5-flash`.

<br>

# Vesper Review

<br>

The main analysis comment is updated in place and keeps a reviewed commits table. Do not create inline reviews when there are no inline suggestions.

<br>

`enable_rag` defaults to `false`. Use RAG only when a PR needs fresh package, security, or docs context.

<br>

`/apply` authoring exists. Automatic suggestion commits stay off by default.

<br>

Command replies use `🙂` for normal, `😅` for blocked or unavailable, and `😴` for paused, skipped, or no-op. Do not use GitHub reactions for command feedback. Mention this rule on the website only at Support -> Command replies.

<br>

PR #176 comments from `2026-05-22` showed this behavior working for `/status`, `/pause`, `/resume`, `/help`, `/apply`, quota notices, and no-suggestion replies.

<br>

# Local

<br>

Python focused test:

<br>

```sh
.venv/bin/python -m pytest test/test_vesper.py
```

<br>

Ruby test command that worked here:

<br>

```sh
/opt/homebrew/opt/ruby/bin/bundle exec rake test
```

<br>

Last Ruby test result: `126 runs, 188 assertions, 0 failures, 0 errors, 0 skips`.

<br>

Default shell Ruby may be Apple Ruby `2.6`. Homebrew Ruby exists at `/opt/homebrew/opt/ruby/bin/ruby`. Bundled gems are in `vendor/bundle`.

<br>

`gh` auth is valid in the macOS keyring, but the Codex sandbox can see a stale token and blocked network. Run `gh` with escalated permissions when PR data is needed.

<br>

Vercel can hit the free daily deploy limit. If live behavior does not match `main`, check deploy age before changing code.

<br>

Next check: when Vercel can deploy again, confirm command comments still have no thumbs-up reactions and quota notices still start with `😅`.
