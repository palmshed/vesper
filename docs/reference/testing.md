# Testing

The test suite is designed to run without real Gemini API calls. Unit tests stub HTTP requests and use test API keys that match the expected format.

## Commands

Run the full test suite:

```bash
bundle exec ruby test/runner.rb
```

Run a single file:

```bash
bundle exec ruby -Ilib:test test/unit/client_test.rb
```

Run the gem build check:

```bash
gem build friday_gemini_ai.gemspec
```

## API Tests

E2E and integration tests that call the real API require `GEMINI_API_KEY`.

```bash
GEMINI_API_KEY=your_key bundle exec rake e2e_test
```

CI skips or stubs network-dependent paths unless the needed secret is available.

## Coverage

Coverage is handled in CI. Local runs should focus on passing tests and clear failures.
