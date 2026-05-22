# Vesper

A Ruby interface to Google's Gemini AI models, designed for simplicity, security, and power.

## Quick Start

Install the gem:

```bash
gem install friday_gemini_ai
```

Set your API key:

```bash
export GEMINI_API_KEY="your-api-key-here"
```

Generate text:

```ruby
require 'vesper'

client = GeminiAI::Client.new
response = client.generate_text("Hello, Gemini!")
puts response
```

## PR Review

[Vesper](reference/vesper.md) automates code reviews using Gemini AI, analyzing PRs and providing feedback.

## Documentation

- [Quick Start](start/quickstart.md)
- [API Reference](reference/api.md)
- [Vesper](reference/vesper.md)
- [Guides](guides/community.md)
- [Testing](reference/testing.md)

## Links

- [RubyGems](https://rubygems.org/gems/friday_gemini_ai)
- [Issues](https://github.com/bniladridas/vesper/issues)
- [Discussions](https://github.com/bniladridas/vesper/discussions)
- [Security](https://github.com/bniladridas/vesper/blob/main/.github/SECURITY.md)
- [License](https://github.com/bniladridas/vesper/blob/main/LICENSE)
