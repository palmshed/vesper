# Vesper
<img src="website/assets/readme-header.png" alt="Vesper" width="100%">


[![Gem](https://img.shields.io/gem/v/friday_gemini_ai?style=flat-square&label=gem)](https://rubygems.org/gems/friday_gemini_ai)
![Ruby](https://img.shields.io/badge/ruby-%3E%3D%203.1-cc342d?style=flat-square)
[![License](https://img.shields.io/badge/license-MIT-2f4858?style=flat-square)](LICENSE)
![Tests](https://img.shields.io/badge/tests-134%20passing-2e7d32?style=flat-square)

Ruby client for Google's Gemini models, with a small CLI and an optional PR-review companion.


<br>

# Installation

```bash
gem install friday_gemini_ai
```

With Bundler:

```ruby
gem 'friday_gemini_ai', require: 'vesper'
```

The package is published as `friday_gemini_ai`. The runtime entrypoint is `vesper`.

Set your API key in `.env`:

```
GEMINI_API_KEY=your_api_key
```

> [!NOTE]
> Ensure your API key is kept secure and not committed to version control.


<br>

# Usage

### Basic Setup

```ruby
require 'vesper'
GeminiAI.load_env

client = GeminiAI::Client.new
puts client.generate_text('Write a haiku about Ruby')
```

Use a different model when needed:

```ruby
fast_client = GeminiAI::Client.new(model: :flash)
puts fast_client.generate_text('Explain Ruby in one sentence')
```

### Model Reference

| Key           | ID                      | Use case                        |
| ------------- | ----------------------- | ------------------------------- |
| `:pro`        | `gemini-2.5-pro`        | Most capable, complex reasoning |
| `:flash`      | `gemini-2.5-flash`      | Fast, general-purpose           |
| `:flash_2_0`  | `gemini-2.0-flash`      | Legacy support                  |
| `:flash_lite` | `gemini-2.0-flash-lite` | Lightweight legacy              |


<br>

# Capabilities

Vesper supports text generation, chat, image-to-text analysis, model aliases, safety settings, API key masking, retry handling, and a local CLI for quick prompts.


<br>

# Handling Errors

Client validation and API failures raise `GeminiAI::Error` with a readable message.
HTTP 429 responses are retried automatically up to three times with exponential backoff.

```ruby
begin
  response = client.generate_text('Hello')
  puts response
rescue GeminiAI::Error => err
  warn "Generation failed: #{err.message}"
end
```

Common failures include:

- Missing or invalid `GEMINI_API_KEY`
- Empty prompts
- Prompts over the configured maximum length
- Gemini API errors returned by the service
- Network errors raised by HTTParty

### Retries

Rate-limit responses (`429`) are retried up to three times with waits of 5, 10, and 20 seconds.

### Timeouts

Requests use a 30 second HTTParty timeout.


<br>

# Logging

```ruby
require 'vesper'

GeminiAI::Client.logger.level = Logger::INFO
client = GeminiAI::Client.new
```


<br>

# Requirements

Ruby 3.1 or later. Linux and macOS are recommended.


<br>

# Environment Variables

```bash
GEMINI_API_KEY=your_api_key_here
VESPER_GEMINI_API_KEY=your_api_key_here
```

### Repo CLI

```bash
./bin/gemini test
./bin/gemini generate "Your prompt"
./bin/gemini chat
```


<br>

# Local Development & Testing

```bash
bundle exec rake test          # Run tests
bundle exec rake rubocop       # Optional lint check
gem build *.gemspec            # Verify build
```


<br>

# PR Review

Vesper is the optional PR-review companion included in this repo. For setup details, see [vesper/Vesper.md](vesper/Vesper.md).


<br>

# Examples

### Text Generation

```ruby
client = GeminiAI::Client.new
puts client.generate_text('Write a haiku about Ruby')
```

### Image Analysis

```ruby
image_data = Base64.strict_encode64(File.binread('path/to/image.jpg'))
puts client.generate_image_text(image_data, 'Describe this image')
```

### Chat

```ruby
messages = [
  { role: 'user', content: 'Hello!' },
  { role: 'model', content: 'Hi there!' },
  { role: 'user', content: 'Tell me about Ruby.' }
]
puts client.chat(messages, system_instruction: 'Be helpful and concise.')
```


<br>

# Documentation

| Need | Link |
| --- | --- |
| Start | [Quickstart](docs/start/quickstart.md) |
| API | [Reference](docs/reference/api.md) |
| Recipes | [Cookbook](docs/reference/cookbook.md) |
| Practice | [Best practices](docs/guides/practices.md) |
| Automation | [Workflows](docs/guides/workflows.md) |
| Project | [Contributing](docs/CONTRIBUTING.md) |


<br>

# Contributing

Fork the repo and open a pull request.


<br>

# License

MIT → see [LICENSE](LICENSE).
