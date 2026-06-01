# Setup Guide

<br>

# API Key Configuration

<br>

# For Development

<br>

1. **Get your Gemini API Key:**
   - Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
   - Create a new API key
   - Copy the key (it should start with `AIza`)

<br>

2. **Set the environment variable:**
   ```bash
   export GEMINI_API_KEY="your_api_key_here"
   ```

<br>

   Or create a `.env` file in the project root:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```

<br>

# For CI/CD (GitHub Actions)

<br>

1. **Add the API key as a repository secret:**
   - Go to your repository on GitHub
   - Navigate to Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `GEMINI_API_KEY`
   - Value: Your actual API key

<br>

2. **The workflow is already configured** to use this secret in `.github/workflows/ci.yml`

<br>

# Testing

<br>

- **All tests** use HTTParty stubbing and don't require a real API key
- Tests run completely offline with mocked responses
- No external dependencies or API keys needed for the full test suite

<br>

# Running Tests

<br>

```bash
# Install dependencies
bundle install

# Run all tests
bundle exec rake test

# Run tests without coverage (faster for development)
bundle exec rake test_no_coverage

# Run specific test suites
bundle exec ruby -Ilib:test test/unit/client_test.rb      # Unit tests
bundle exec ruby -Ilib:test test/integration/api.rb      # Integration tests
```
