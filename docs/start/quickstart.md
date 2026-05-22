# Quickstart

Get started with Vesper in minutes.

## Prerequisites

- Ruby 3.1 or higher
- Google AI API key from [Google AI Studio](https://aistudio.google.com/app/apikey)

## Installation

Install the gem:

```bash
gem install friday_gemini_ai
```

Or add to Gemfile:

```ruby
gem 'friday_gemini_ai', require: 'vesper'
```

## Get API Key

Create an API key in [Google AI Studio](https://aistudio.google.com/app/apikey), then keep it outside source control.

## Setup Environment

Create `.env` file:

```bash
echo "GEMINI_API_KEY=your_api_key_here" > .env
```

Replace with your actual key.

## First Request

Create a Ruby file:

```ruby
require 'vesper'

client = GeminiAI::Client.new
response = client.generate_text("Hello, world!")
puts response
```

Run it:

```bash
ruby your_file.rb
```

## Test CLI

Test with the repo CLI:

```bash
./bin/gemini test
```

It should print a short success response when the API key is valid.

## Examples

Creative content:

```ruby
response = client.generate_text(
  "Write a story",
  temperature: 0.8
)
```

Conversation:

```ruby
messages = [
  { role: 'user', content: 'What is Ruby?' }
]
response = client.chat(messages)
```

Interactive chat:

```bash
./bin/gemini chat
```

## Common Issues

- API key required: Check `.env` file
- Invalid key: Ensure starts with `AIza`
- CLI permission: Run `chmod +x bin/gemini`

## Next Steps

- [Usage Guide](../reference/usage.md)
- [API Reference](../reference/api.md)
- [Models](../reference/models.md)
- [Troubleshooting](../guides/troubleshoot.md)
