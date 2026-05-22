# State

## Project shape

The published gem is `friday_gemini_ai`.

The runtime entrypoint is `vesper`.

The GitHub App is `Vesper Review`.

Gem releases use tags like `friday_gemini_ai/v1.7.1`. The app is deployed from `main` and should be treated as build/commit based, not gem-release based.

## Current behavior notes

Vesper command replies are meant to stay quiet and prose-like.

Use `🙂` for normal replies, `😅` for blocked or unavailable states, and `😴` for paused, skipped, or no-op states.

Do not use GitHub reactions for command feedback.

The main Vesper analysis comment is updated in place and keeps a reviewed commits table.

Empty inline reviews should be skipped when there are no inline suggestions.

## Operations

Vercel production deploys may hit the free daily deployment limit. If live behavior does not match `main`, check Vercel deployment age before changing code.

Run focused tests with:

```sh
.venv/bin/python -m pytest test/test_vesper.py
```

Pushes run the pre-push checks.

## Next checks

When Vercel can deploy again, verify that command comments no longer get thumbs-up reactions and that quota notices include `😅`.
