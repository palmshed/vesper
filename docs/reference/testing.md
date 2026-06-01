# Testing

<br>

The test suite is designed to run without real Gemini API calls. Unit tests stub HTTP requests and use test API keys that match the expected format.

<br>

# Commands

<br>

Run the full test suite:

<br>

```bash
bundle exec ruby test/runner.rb
```

<br>

Run a single file:

<br>

```bash
bundle exec ruby -Ilib:test test/unit/client_test.rb
```

<br>

Run the gem build check:

<br>

```bash
gem build friday_gemini_ai.gemspec
```

<br>

# API Tests

<br>

E2E and integration tests that call the real API require `GEMINI_API_KEY`.

<br>

```bash
GEMINI_API_KEY=your_key bundle exec rake e2e_test
```

<br>

CI skips or stubs network-dependent paths unless the needed secret is available.

<br>

# Coverage

<br>

Coverage is handled in CI. Local runs should focus on passing tests and clear failures.
