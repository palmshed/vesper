# Usage

## Getting Started

### 1. Installation

```bash
gem install friday_gemini_ai
```

### 2. Get API Key

1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Create a new API key
3. Set it as environment variable or in .env file

### 3. Basic Setup

Create a `.env` file:
```
GEMINI_API_KEY=your_api_key_here
```

## Basic Usage

### Simple Text Generation

```ruby
require 'vesper'

# Load environment variables
GeminiAI.load_env

# Create client and generate text
client = GeminiAI::Client.new
response = client.generate_text("Write a haiku about programming")
puts response
```

### Chat Conversations

```ruby
client = GeminiAI::Client.new
messages = [
  { role: 'user', content: 'Hello, what is Ruby?' },
  { role: 'model', content: 'Ruby is a programming language.' },
  { role: 'user', content: 'What makes it special?' }
]

response = client.chat(messages)
puts response
```

## Advanced Usage

### Custom Parameters

```ruby
# Creative writing (high temperature)
creative_response = client.generate_text(
  "Write a story about a robot",
  temperature: 0.9,      # More creative
  max_tokens: 200,       # Longer response
  top_p: 0.95,          # More diverse
  top_k: 50             # Consider more options
)

# Factual responses (low temperature)
factual_response = client.generate_text(
  "Explain quantum computing",
  temperature: 0.1,      # More deterministic
  max_tokens: 100,       # Shorter response
  top_p: 0.8,           # Less diverse
  top_k: 20             # Consider fewer options
)
```

### Different Models

```ruby
# Default model
pro_client = GeminiAI::Client.new

# Fast model
flash_client = GeminiAI::Client.new(model: :flash)

# Flash Lite model (faster, lighter)
lite_client = GeminiAI::Client.new(model: :flash_lite)

# Compare responses
pro_response = pro_client.generate_text("Explain AI")
flash_response = flash_client.generate_text("Explain AI")
lite_response = lite_client.generate_text("Explain AI")
```

### Error Handling

```ruby
begin
  client = GeminiAI::Client.new
  response = client.generate_text("Your prompt")
  puts response
rescue GeminiAI::AuthenticationError => e
  puts "API key error: #{e.message}"
rescue GeminiAI::APIError => e
  puts "API error: #{e.message}"
rescue GeminiAI::NetworkError => e
  puts "Network error: #{e.message}"
rescue GeminiAI::Error => e
  puts "General error: #{e.message}"
end
```

### Batch Processing

```ruby
client = GeminiAI::Client.new
prompts = [
  "Write a haiku about coding",
  "Explain recursion briefly",
  "Compare Ruby and Python."
]

prompts.each_with_index do |prompt, index|
  begin
    response = client.generate_text(prompt)
    puts "#{index + 1}. #{prompt}"
    puts "   Response: #{response}\n\n"
  rescue => e
    puts "#{index + 1}. Error: #{e.message}\n\n"
  end
end
```

## CLI Usage

### Test Connection

```bash
./bin/gemini test
```

### Generate Text

```bash
./bin/gemini generate "Write a joke about programming"
```

### Interactive Chat

```bash
./bin/gemini chat
```

This starts an interactive session where you can have a conversation with the AI.

### Help

```bash
./bin/gemini help
```

## Configuration Options

### Environment Variables

- `GEMINI_API_KEY`: Your API key (required)
- `RAILS_ENV` / `RACK_ENV`: Environment detection for logging levels

### Logging Levels

- **Production**: ERROR only
- **Test**: WARN and above
- **Development**: DEBUG (all messages)

### Model Options

| Model | Speed | Quality | Use Case |
|-------|-------|---------|----------|
| `:pro` | Medium | High | Default |
| `:flash` | Fast | Good | General purpose |
| `:flash_lite` | Fast | Good | Quick responses |

## Best Practices

### 1. API Key Security

```ruby
# Good - Use environment variables
client = GeminiAI::Client.new

# Bad - Hardcode API key
client = GeminiAI::Client.new('AIza...')
```

### 2. Error Handling

```ruby
# Good - Handle specific errors
begin
  response = client.generate_text(prompt)
rescue GeminiAI::AuthenticationError
  # Handle auth error
rescue GeminiAI::APIError
  # Handle API error
end

# Bad - Catch all errors
begin
  response = client.generate_text(prompt)
rescue => e
  # Too broad
end
```

### 3. Parameter Tuning

```ruby
# For creative tasks
temperature: 0.7-0.9
top_p: 0.9-0.95
top_k: 40-50

# For factual tasks
temperature: 0.1-0.3
top_p: 0.8-0.9
top_k: 20-30
```

### 4. Prompt Engineering

```ruby
# Good - Clear, specific prompts
"Write a haiku about Ruby programming with 5-7-5 syllable structure"

# Bad - Vague prompts
"Write something about Ruby"
```

## Troubleshooting

### Common Issues

1. **"API key is required"**
   - Set `GEMINI_API_KEY` environment variable
   - Check .env file is loaded with `GeminiAI.load_env`

2. **"Invalid API key format"**
   - Ensure API key starts with "AIza"
   - Check for extra spaces or characters

3. **"Prompt cannot be empty"**
   - Provide non-empty string to `generate_text`

4. **Network timeouts**
   - Check internet connection
   - API has 30-second timeout built-in

### Debug Logging

Enable debug logging to see request and response details:

```ruby
GeminiAI::Utils::Logger.instance.level = Logger::DEBUG
```

## Request Tips

1. **Use Flash Lite for lower latency** when the task is small
2. **Adjust max_tokens** to limit response length
3. **Batch related requests** in sequence
4. **Cache repeated responses** locally

## Integration Examples

### Rails Application

```ruby
# app/services/ai_service.rb
class AiService
  def initialize
    @client = GeminiAI::Client.new
  end

  def generate_content(prompt)
    @client.generate_text(prompt)
  rescue GeminiAI::Error => e
    Rails.logger.error "AI Service Error: #{e.message}"
    "Sorry, I couldn't generate content right now."
  end
end
```

### Sinatra Application

```ruby
require 'sinatra'
require 'vesper'

GeminiAI.load_env

post '/generate' do
  client = GeminiAI::Client.new
  response = client.generate_text(params[:prompt])
  { response: response }.to_json
rescue GeminiAI::Error => e
  status 500
  { error: e.message }.to_json
end
```
