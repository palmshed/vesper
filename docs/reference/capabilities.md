# Core Capabilities

Vesper provides comprehensive access to Google Gemini's advanced AI capabilities through a Ruby interface.

## Text Generation

Generate high-quality text for various use cases with fine-grained control over output characteristics.

### Basic Text Generation
```ruby
client = GeminiAI::Client.new
response = client.generate_text("Explain quantum computing in simple terms")
```

### Creative Writing
```ruby
creative_response = client.generate_text(
  "Write a mystery story opening",
  temperature: 0.8,      # High creativity
  max_tokens: 300,       # Longer response
  top_p: 0.9            # Diverse vocabulary
)
```

### Technical Documentation
```ruby
technical_response = client.generate_text(
  "Document this Ruby method: def calculate_fibonacci(n)",
  temperature: 0.3,      # More deterministic
  max_tokens: 200,       # Focused length
  top_k: 30             # Precise vocabulary
)
```

## Chat Conversations

Build interactive conversational experiences with context awareness and multi-turn dialogue support.

### Simple Chat
```ruby
messages = [
  { role: 'user', content: 'Hello! How are you?' },
  { role: 'model', content: 'Hello! I\'m doing well, thank you.' },
  { role: 'user', content: 'Can you help me with Ruby programming?' }
]

response = client.chat(messages)
```

### Contextual Conversations
```ruby
# Build conversation history
conversation = []

# User asks initial question
conversation << { role: 'user', content: 'What is object-oriented programming?' }
response1 = client.chat(conversation)
conversation << { role: 'model', content: response1 }

# Follow-up question with context
conversation << { role: 'user', content: 'Can you give me a Ruby example?' }
response2 = client.chat(conversation)
conversation << { role: 'model', content: response2 }

# Context is maintained throughout
conversation << { role: 'user', content: 'How does inheritance work in that example?' }
response3 = client.chat(conversation)
```

### Specialized Chat Roles
```ruby
# Technical assistant
tech_messages = [
  { role: 'user', content: 'You are a Ruby expert. Help me optimize this code.' },
  { role: 'model', content: 'I\'d be happy to help optimize your Ruby code.' },
  { role: 'user', content: 'Here\'s my code: [code snippet]' }
]

# Creative writing assistant
creative_messages = [
  { role: 'user', content: 'You are a creative writing coach. Help me improve my story.' },
  { role: 'model', content: 'I\'m excited to help with your creative writing!' },
  { role: 'user', content: 'Here\'s my story draft: [story text]' }
]
```

## Long Context Processing

Handle large amounts of text and maintain context across extended conversations.

### Document Analysis
```ruby
long_document = File.read('large_document.txt')
analysis = client.generate_text(
  "Summarize the key points from this document: #{long_document}",
  max_tokens: 500
)
```

### Code Review
```ruby
code_file = File.read('complex_application.rb')
review = client.generate_text(
  "Review this Ruby code for best practices and potential issues: #{code_file}",
  temperature: 0.2,  # Focused analysis
  max_tokens: 400
)
```

## Structured Output

Generate responses in specific formats for integration with other systems.

### JSON Output
```ruby
json_response = client.generate_text(
  "Generate a JSON object with user profile data for a Ruby developer",
  temperature: 0.1  # Consistent structure
)
```

### Markdown Documentation
```ruby
docs = client.generate_text(
  "Create markdown documentation for a Ruby gem that handles file uploads",
  temperature: 0.4,
  max_tokens: 600
)
```

### Code Generation
```ruby
ruby_code = client.generate_text(
  "Generate a Ruby class for handling HTTP requests with error handling",
  temperature: 0.3,
  max_tokens: 300
)
```

## Advanced Features

### Parameter Optimization
```ruby
# For factual accuracy
factual_client = GeminiAI::Client.new
factual_response = factual_client.generate_text(
  "What are the key features of Ruby 3.2?",
  temperature: 0.1,   # Low randomness
  top_p: 0.8,        # Focused sampling
  top_k: 20          # Limited vocabulary
)

# For creative tasks
creative_client = GeminiAI::Client.new
creative_response = creative_client.generate_text(
  "Write a poem about programming",
  temperature: 0.9,   # High creativity
  top_p: 0.95,       # Diverse sampling
  top_k: 50          # Full vocabulary
)
```

### Batch Processing
```ruby
prompts = [
  "Explain Ruby blocks",
  "What are Ruby gems?",
  "How does Ruby garbage collection work?"
]

responses = prompts.map do |prompt|
  client.generate_text(prompt, temperature: 0.3)
end
```

### Error Recovery
```ruby
def robust_generation(prompt, retries: 3)
  attempt = 0
  begin
    client.generate_text(prompt)
  rescue GeminiAI::RateLimitError => e
    attempt += 1
    if attempt <= retries
      sleep(2 ** attempt)  # Exponential backoff
      retry
    else
      raise e
    end
  end
end
```

## Performance Optimization

### Response Caching
```ruby
class CachedClient
  def initialize
    @client = GeminiAI::Client.new
    @cache = {}
  end

  def generate_text(prompt, options = {})
    cache_key = "#{prompt}:#{options.hash}"
    @cache[cache_key] ||= @client.generate_text(prompt, options)
  end
end
```

### Streaming Responses (Conceptual)
```ruby
# For long responses, process in chunks
def process_long_response(prompt)
  response = client.generate_text(prompt, max_tokens: 1000)

  # Process response in chunks
  response.scan(/.{1,100}/).each do |chunk|
    yield chunk if block_given?
  end
end

process_long_response("Write a detailed essay about Ruby") do |chunk|
  puts chunk
  sleep(0.1)  # Simulate streaming
end
```

## Integration Patterns

### Rails Integration
```ruby
class AiController < ApplicationController
  def generate
    client = GeminiAI::Client.new
    response = client.generate_text(params[:prompt])
    render json: { response: response }
  rescue GeminiAI::Error => e
    render json: { error: e.message }, status: 500
  end
end
```

### Background Jobs
```ruby
class AiGenerationJob < ApplicationJob
  def perform(prompt, user_id)
    client = GeminiAI::Client.new
    response = client.generate_text(prompt)

    # Store result
    AiResponse.create!(
      user_id: user_id,
      prompt: prompt,
      response: response
    )
  end
end
```

### Webhook Processing
```ruby
class WebhookProcessor
  def process_content(webhook_data)
    client = GeminiAI::Client.new

    analysis = client.generate_text(
      "Analyze this webhook data: #{webhook_data}",
      temperature: 0.2
    )

    # Process analysis result
    handle_analysis(analysis)
  end
end
```

## Security Considerations

### Input Sanitization
```ruby
def safe_generate(user_input)
  # Sanitize input
  clean_input = user_input.gsub(/[<>]/, '')

  # Limit length
  clean_input = clean_input[0..1000] if clean_input.length > 1000

  client.generate_text(clean_input)
end
```

### API Key Protection
```ruby
# Good - Environment variables
client = GeminiAI::Client.new

# Bad - Hardcoded keys
# client = GeminiAI::Client.new('AIza...')

# Good - Key validation
begin
  client = GeminiAI::Client.new
rescue GeminiAI::AuthenticationError
  Rails.logger.error "Invalid API key configuration"
  raise "AI service unavailable"
end
```

## Monitoring and Logging

### Request Tracking
```ruby
class TrackedClient
  def initialize
    @client = GeminiAI::Client.new
    @request_count = 0
  end

  def generate_text(prompt, options = {})
    @request_count += 1
    start_time = Time.now

    response = @client.generate_text(prompt, options)

    duration = Time.now - start_time
    Rails.logger.info "AI Request ##{@request_count}: #{duration}s"

    response
  end
end
```

### Error Monitoring
```ruby
def monitored_generation(prompt)
  client.generate_text(prompt)
rescue GeminiAI::RateLimitError => e
  ErrorTracker.notify("Rate limit exceeded", context: { prompt: prompt })
  raise e
rescue GeminiAI::APIError => e
  ErrorTracker.notify("API error", context: { error: e.message })
  raise e
end
```
