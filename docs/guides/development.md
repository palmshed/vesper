# Development Guide

This guide covers the setup and development of the Vesper Ruby gem.

## Local Development Setup

### Prerequisites
1. Ruby 3.1+ (check `.ruby-version` for the local development version)
2. Bundler (`gem install bundler`)
3. Git
4. [GitHub CLI](https://cli.github.com/) (recommended for PR management)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/bniladridas/vesper.git
   cd vesper
   ```

2. Install dependencies:
   ```bash
   bundle install
   ```

3. Set up your environment:
   ```bash
   cp .env.example .env
   # Edit .env and add your GEMINI_API_KEY
   ```

## Running Tests

Run the full test suite:
```bash
bundle exec rake test
```

Run a specific test file:
```bash
bundle exec ruby -Ilib:test test/unit/client_test.rb
```

## Linting and Code Style

Run RuboCop when changing Ruby code:
```bash
bundle exec rubocop
bundle exec rubocop -a
```

## Development Workflow

1. Create a new branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and write tests

3. Run tests and linters:
   ```bash
   bundle exec rake test
   bundle exec rubocop
   ```

4. Commit your changes with a descriptive message

5. Push your branch and create a pull request

## GitHub Actions Integration

The project uses GitHub Actions for CI/CD. Key workflows:

1. **CI Workflow** (`.github/workflows/ci.yml`):
     - Runs on push and pull requests
     - Tests on multiple Ruby versions
     - Runs security checks (linting temporarily disabled due to bundler issues)

2. **Vesper Workflow** (`.github/workflows/vesper.yml`):
    - Automated PR analysis and code review
    - Provides intelligent feedback on code quality, security, and performance
    - Uses Gemini AI for comprehensive analysis

3. **Release Workflow** (`.github/workflows/release.yml`):
    - Publishes the gem to RubyGems on version tag push

4. **Security Workflow** (`.github/workflows/security.yml`):
    - Runs security scans and dependency checks

## Security Considerations

1. **API Key Security**:
   - Never commit API keys to version control
   - Use environment variables for configuration
   - The gem automatically masks API keys in logs

2. **Dependencies**:
   - All dependencies are pinned in the Gemfile.lock
   - Regular security updates via Dependabot

3. **Code Review**:
   - All PRs require at least one review
   - Automated tests must pass before merging
   - Code style must follow RuboCop guidelines

## Debugging

Enable debug logging:
```ruby
GeminiAI::Client.logger.level = Logger::DEBUG
```

## Building the Gem

Build the gem locally:
```bash
gem build friday_gemini_ai.gemspec
```

Install the built gem:
```bash
gem install friday_gemini_ai-*.gem
```

## Release Process

1. Update the version in `lib/core/version.rb`
2. Update `docs/CHANGELOG.md` when release notes are needed
3. Commit changes with message "Bump version to x.y.z"
4. Create a git tag:
   ```bash
   git tag -a vx.y.z -m "Version x.y.z"
   git push origin vx.y.z
   ```
5. The release workflow will automatically publish to RubyGems
