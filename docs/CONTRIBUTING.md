# Contributing

Contributions are welcome when they keep the project small, clear, and tested.

Please read the [`Code of Conduct`](https://github.com/bniladridas/vesper/blob/main/docs/CODE_OF_CONDUCT.md) before participating.

## Setup

Clone the repository, install the bundle, and copy the example environment file.

```bash
git clone https://github.com/bniladridas/vesper.git
cd vesper
bundle install
cp config/.env.example .env
```

Add `GEMINI_API_KEY` to `.env` when running integration examples or tests that call the API.

## Checks

Run the checks that fit your change. Most code changes should pass the test runner and RuboCop before review.

```bash
bundle exec ruby test/runner.rb
bundle exec rubocop
```

Run the audit when dependencies change.

```bash
bundle exec bundle-audit
```

For documentation changes, build the docs locally.

```bash
bundle exec rake docs
```

## Pull Requests

Keep pull requests focused on one issue or task. Include tests when behavior changes, and update documentation when usage changes. Avoid committing secrets, generated files, local config, or unrelated cleanup.

Use clear commit messages. Conventional Commit format is fine, but plain wording is more important than ceremony.

## Issues

For bugs, include the Ruby version, Vesper version, operating system, reproduction steps, and the expected and actual behavior.

For feature requests, describe the use case and the smallest API that would solve it.

## References

| Topic | Link |
| --- | --- |
| Setup | [`Setup`](https://github.com/bniladridas/vesper/blob/main/docs/SETUP.md) |
| Practices | [`Development practices`](https://github.com/bniladridas/vesper/blob/main/docs/guides/practices.md) |
| Tests | [`Testing`](https://github.com/bniladridas/vesper/blob/main/docs/reference/testing.md) |
| API | [`API reference`](https://github.com/bniladridas/vesper/blob/main/docs/reference/api.md) |

## License

By contributing, you agree that your contributions are licensed under the MIT License.
