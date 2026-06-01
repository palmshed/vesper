# Quickstart

<br>

Get started with Vesper in minutes.

<br>

# Prerequisites

<br>

- Ruby 3.3 or higher
- Google AI API key from [Google AI Studio](https://aistudio.google.com/app/apikey)

<br>

# Installation

<br>

Install the gem:

<br>

```bash
gem install friday_gemini_ai
```

<br>

Or add to Gemfile:

<br>

```ruby
gem 'friday_gemini_ai', require: 'vesper'
```

<br>

# Get API Key

<br>

Create an API key in [Google AI Studio](https://aistudio.google.com/app/apikey), then keep it outside source control.

<br>

# Setup Environment

<br>

Create `.env` file:

<br>

```bash
echo "GEMINI_API_KEY=your_api_key_here" > .env
```

<br>

Replace with your actual key.

<br>

# First Request

<br>

Create a Ruby file:

<br>

```ruby
require 'vesper'

client = GeminiAI::Client.new
response = client.generate_text("Hello, world!")
puts response
```

<br>

Run it:

<br>

```bash
ruby your_file.rb
```

<br>

# Test CLI

<br>

Test with the repo CLI:

<br>

```bash
./bin/gemini test
```

<br>

It should print a short success response when the API key is valid.

<br>

# Examples

<br>

Creative content:

<br>

```ruby
response = client.generate_text(
  "Write a story",
  temperature: 0.8
)
```

<br>

Conversation:

<br>

```ruby
messages = [
  { role: 'user', content: 'What is Ruby?' }
]
response = client.chat(messages)
```

<br>

Interactive chat:

<br>

```bash
./bin/gemini chat
```

<br>

# Common Issues

<br>

- API key required: Check `.env` file
- Invalid key: Ensure starts with `AIza`
- CLI permission: Run `chmod +x bin/gemini`

<br>

# Next Steps

<br>

- [`Usage Guide`](../reference/usage.md)
- [`API Reference`](../reference/api.md)
- [`Models`](../reference/models.md)
- [`Troubleshooting`](../guides/troubleshoot.md)
