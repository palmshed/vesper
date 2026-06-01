# API Reference

<br>

Ruby interface to Google's Gemini AI models.

<br>

# Installation

<br>

```ruby
gem install friday_gemini_ai
```

<br>

Or in Gemfile:

<br>

```ruby
gem 'friday_gemini_ai', require: 'vesper'
```

<br>

# Quick Start

<br>

```ruby
require 'vesper'

client = GeminiAI::Client.new
response = client.generate_text("Hello, world!")
puts response
```

<br>

# Client Class

<br>

# Constructor

<br>

```ruby
GeminiAI::Client.new(api_key = nil, model: :pro)
```

<br>

Parameters:
- `api_key`: API key string (optional, uses ENV if not provided)
- `model`: Model symbol (optional, default :pro)

<br>

Examples:

<br>

```ruby
client = GeminiAI::Client.new
client = GeminiAI::Client.new('your_key')
client = GeminiAI::Client.new(model: :flash)
```

<br>

# Methods

<br>

# generate_text(prompt, options = {})

<br>

Generate text from prompt.

<br>

Parameters:
- `prompt`: String prompt
- `options`: Hash of options

<br>

Options:
- `temperature`: Float (0.0-1.0, default 0.7)
- `max_tokens`: Integer (default 1024)
- `top_p`: Float (default 0.9)
- `top_k`: Integer (default 40)

<br>

Returns: String response

<br>

Examples:

<br>

```ruby
response = client.generate_text("Write a haiku")
response = client.generate_text("Explain AI", temperature: 0.3)
```

<br>

# `chat(messages, options = {})`

<br>

Conduct a multi-turn conversation.

<br>

**Parameters:**
- `messages` (Array): Array of message hashes
- `options` (Hash, optional): Same as `generate_text`

<br>

**Message Format:**
```ruby
{
  role: 'user' | 'model',
  content: 'message text'
}
```

<br>

**Returns:** String - AI response

<br>

**Example:**
```ruby
messages = [
  { role: 'user', content: 'Hello' },
  { role: 'model', content: 'Hi there!' },
  { role: 'user', content: 'How are you?' }
]

response = client.chat(messages)
```

<br>

# `generate_image_text(image_base64, prompt, options = {})`

<br>

Analyze an image with a text prompt.

<br>

**Parameters:**
- `image_base64` (String): Base64 encoded image data
- `prompt` (String): Text prompt about the image
- `options` (Hash, optional): Same as `generate_text`

<br>

**Returns:** String - Analysis response

<br>

**Example:**
```ruby
image_data = Base64.encode64(File.read('image.jpg'))
response = client.generate_image_text(image_data, "What's in this image?")
```

<br>

# Error Classes

<br>

| Error Class | Description |
| ----------- | ----------- |
| `GeminiAI::Error` | Base error class for all gem-related errors |
| `GeminiAI::APIError` | Raised when API returns an error response |
| `GeminiAI::AuthenticationError` | Raised when API key is invalid or missing |
| `GeminiAI::RateLimitError` | Raised when API rate limit is exceeded |
| `GeminiAI::InvalidRequestError` | Raised when request parameters are invalid |
| `GeminiAI::NetworkError` | Raised when network communication fails |

<br>

# Utility Classes

<br>

# `GeminiAI::Utils::Loader`

<br>

Utility for loading environment variables from .env files.

<br>

```ruby
GeminiAI::Utils::Loader.load('.env')
# or
GeminiAI.load_env('.env')
```

<br>

# `GeminiAI::Utils::Logger`

<br>

Centralized logging utility with API key masking.

<br>

```ruby
GeminiAI::Utils::Logger.info("Message")
GeminiAI::Utils::Logger.debug("Debug info")
```

<br>

# Models

<br>

# Available Models

<br>

| Symbol | Model ID | Description |
| ------ | -------- | ----------- |
| `:flash_latest` | `gemini-flash-latest` | Moving Flash alias |
| `:pro_latest` | `gemini-pro-latest` | Moving Pro alias |
| `:flash_3_5` | `gemini-3.5-flash` | Gemini 3.5 Flash |
| `:pro_3_preview` | `gemini-3-pro-preview` | Gemini 3 preview |
| `:flash_3_preview` | `gemini-3-flash-preview` | Gemini 3 Flash preview |
| `:pro_3_1_preview` | `gemini-3.1-pro-preview` | Gemini 3.1 Pro preview |
| `:flash_3_1_lite` | `gemini-3.1-flash-lite` | Gemini 3.1 Flash Lite |
| `:pro_2_5` | `gemini-2.5-pro` | Gemini 2.5 Pro |
| `:flash_2_5` | `gemini-2.5-flash` | Gemini 2.5 Flash |
| `:flash_2_0` | `gemini-2.0-flash` | Gemini 2.0 Flash |
| `:pro` | `gemini-pro-latest` | Short alias |
| `:flash` | `gemini-3.5-flash` | Short alias |
| `:flash_lite` | `gemini-3.1-flash-lite` | Short alias |
| `:pro_2_0` | `gemini-2.0-flash` | Legacy alias |

<br>

# Model Selection

<br>

```ruby
# Default (pro/flash)
client = GeminiAI::Client.new

# Lite model for faster responses
client = GeminiAI::Client.new(model: :flash_lite)
```

<br>

# Configuration

<br>

# Environment Variables

<br>

| Variable | Description | Required |
| -------- | ----------- | -------- |
| `GEMINI_API_KEY` | Your Google Gemini API key | Yes |

<br>

# .env File Support

<br>

Create a `.env` file in your project root:
```
GEMINI_API_KEY=your_api_key_here
```

<br>

Load it in your code:
```ruby
GeminiAI.load_env
```

<br>

# Error Handling

<br>

```ruby
begin
  client = GeminiAI::Client.new
  response = client.generate_text("Hello")
rescue GeminiAI::AuthenticationError => e
  puts "Invalid API key: #{e.message}"
rescue GeminiAI::APIError => e
  puts "API error: #{e.message}"
rescue GeminiAI::Error => e
  puts "Gemini AI error: #{e.message}"
end
```

<br>

# CLI Usage

<br>

The gem includes a command-line interface:

<br>

```bash
# Test connection
./bin/gemini test

# Generate text
./bin/gemini generate "Your prompt here"

# Interactive chat
./bin/gemini chat

# Help
./bin/gemini help
```

<br>

# Examples

<br>

See the `examples/` directory for usage examples:
- `examples/basic_usage.rb` - Basic text generation and chat
- `examples/advanced.rb` - Configuration and error handling
