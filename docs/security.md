# Security

Security reports should be handled privately.

Do not open a public issue for a vulnerability. Use [GitHub Security Advisories](https://github.com/palmshed/vesper/security/advisories/new).

If that is not available, contact the maintainer through GitHub with enough context to start triage.

## Supported Versions

Security fixes target the latest released version and the current `main` branch. Older releases may receive fixes when the change is small and the affected version is still practical to patch.

## Reports

A useful report explains the affected version, environment, impact, and reproduction steps. A small proof of concept is helpful when it is safe to share privately.

Include any known workaround if one exists. If you have a suggested fix, include it as context, but do not open a public pull request before the issue is triaged.

## Handling

Reports are reviewed privately. The fix is prepared, tested, and released before public disclosure when disclosure is needed.

Security updates are released as patch versions when possible. Users should run the latest patch version available for their chosen release line.

## Project Practices

API keys should stay in environment variables or a secret manager. The project masks keys in logs, avoids committing local config, and uses dependency and secret scanning in CI.

Use `bundle audit` when dependencies change:

```bash
bundle exec bundle-audit
```
