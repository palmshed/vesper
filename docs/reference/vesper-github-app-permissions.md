# Vesper Review GitHub App Permissions (Webhook Mode)

Use the smallest set of GitHub App permissions needed for Vesper to review PRs and (optionally) merge them.

## Recommended (Vesper can merge PRs)

| Permission area (GitHub App) | Set to (mark) | Can be unmarked? |
|---|---:|---:|
| Repository metadata | Read-only | No (GitHub requires) |
| Pull requests | Read & write | No |
| Issues | Read & write | No |
| Contents | Read & write | No (needed for merge/authoring flows) |
| Everything else (Actions, Checks, Deployments, Environments, Workflows, Administration, Hooks, Secrets, Security events, Dependabot, Codespaces, Projects, Discussions, Packages, Pages, etc.) | No access | Yes (should be unmarked) |

## If you **do not** merge or author changes

- Keep `Pull requests: Read & write` and `Issues: Read & write`.
- Set `Contents` to `Read-only` (or `No access` if your deployment never reads file contents).

## Webhook events to subscribe

- `Pull request`
- `Issue comment`
