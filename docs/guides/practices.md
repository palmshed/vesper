# Best Practices

<br>

Comprehensive guides for getting the most out of Vesper.

<br>

> [!IMPORTANT]
> Following these practices ensures secure, efficient, and reliable use of the Gemini AI API.

<br>

# Security Best Practices

<br>

# API Key Management

<br>

# Environment Variables (Recommended)
```ruby
# Good - Use environment variables
export GEMINI_API_KEY="your_api_key_here"

# In your Ruby code
client = GeminiAI::Client.new  # Automatically uses ENV['GEMINI_API_KEY']
```

<br>

# .env Files
```ruby
# Good - Use .env files for development
# .env file:
GEMINI_API_KEY=your_api_key_here

# Load in your application
GeminiAI.load_env
client = GeminiAI::Client.new
```

<br>

# What to Avoid

<br>

| Anti-pattern | Reason | Alternative |
| ------------ | ------ | ----------- |
| Hardcoded API keys | Security risk, exposed in code | Use environment variables |
| API keys in version control | Accidental exposure | Use .env files (gitignored) |
| API keys in logs | Logging sensitive data | Use masked logging |

<br>

# Input Validation

<br>

# Sanitize User Input
```ruby
def safe_prompt(user_input)
  # Remove potentially harmful characters
  clean_input = user_input.gsub(/[<>\"']/, '')

  # Limit input length
  clean_input = clean_input[0..2000] if clean_input.length > 2000

  # Validate input is not empty
  raise ArgumentError, "Input cannot be empty" if clean_input.strip.empty?

  clean_input
end

# Usage
user_prompt = params[:prompt]
safe_input = safe_prompt(user_prompt)
response = client.generate_text(safe_input)
```

<br>

# Rate Limiting
```ruby
class RateLimitedClient
  def initialize
    @client = GeminiAI::Client.new
    @requests = []
  end

  def generate_text(prompt, options = {})
    # Remove requests older than 1 minute
    @requests.reject! { |time| time < Time.now - 60 }

    # Check rate limit (60 requests per minute)
    if @requests.length >= 60
      raise "Rate limit exceeded. Try again later."
    end

    @requests << Time.now
    @client.generate_text(prompt, options)
  end
end
```

<br>

# Performance Optimization

<br>

# Response Caching

<br>

# Simple Memory Cache
```ruby
class CachedGeminiClient
  def initialize
    @client = GeminiAI::Client.new
    @cache = {}
  end

  def generate_text(prompt, options = {})
    cache_key = Digest::MD5.hexdigest("#{prompt}:#{options}")

    @cache[cache_key] ||= @client.generate_text(prompt, options)
  end

  def clear_cache
    @cache.clear
  end
end
```

<br>

# Redis Cache
```ruby
require 'redis'

class RedisGeminiClient
  def initialize
    @client = GeminiAI::Client.new
    @redis = Redis.new
  end

  def generate_text(prompt, options = {})
    cache_key = "gemini:#{Digest::MD5.hexdigest("#{prompt}:#{options}")}"

    # Try cache first
    cached = @redis.get(cache_key)
    return cached if cached

    # Generate and cache
    response = @client.generate_text(prompt, options)
    @redis.setex(cache_key, 3600, response)  # Cache for 1 hour

    response
  end
end
```

<br>

# Batch Processing

<br>

# Sequential Processing
```ruby
def process_prompts(prompts)
  client = GeminiAI::Client.new
  results = []

  prompts.each_with_index do |prompt, index|
    begin
      response = client.generate_text(prompt)
      results << { index: index, prompt: prompt, response: response }

      # Add delay to respect rate limits
      sleep(1) if index < prompts.length - 1

    rescue GeminiAI::Error => e
      results << { index: index, prompt: prompt, error: e.message }
    end
  end

  results
end
```

<br>

# Parallel Processing with Thread Pool
```ruby
require 'concurrent-ruby'

def process_prompts_parallel(prompts, max_threads: 5)
  client = GeminiAI::Client.new
  executor = Concurrent::ThreadPoolExecutor.new(
    min_threads: 1,
    max_threads: max_threads,
    max_queue: prompts.length
  )

  futures = prompts.map.with_index do |prompt, index|
    Concurrent::Future.execute(executor: executor) do
      begin
        response = client.generate_text(prompt)
        { index: index, prompt: prompt, response: response }
      rescue GeminiAI::Error => e
        { index: index, prompt: prompt, error: e.message }
      end
    end
  end

  # Wait for all to complete
  results = futures.map(&:value)
  executor.shutdown

  results
end
```

<br>

# Error Handling Strategies

<br>

# Comprehensive Error Handling
```ruby
def generate_with_retry(prompt, max_retries: 3)
  retries = 0

  begin
    client = GeminiAI::Client.new
    client.generate_text(prompt)

  rescue GeminiAI::AuthenticationError => e
    # Don't retry authentication errors
    Rails.logger.error "Authentication failed: #{e.message}"
    raise "AI service authentication failed"

  rescue GeminiAI::RateLimitError => e
    retries += 1
    if retries <= max_retries
      wait_time = 2 ** retries  # Exponential backoff
      Rails.logger.warn "Rate limited, retrying in #{wait_time}s (attempt #{retries})"
      sleep(wait_time)
      retry
    else
      Rails.logger.error "Rate limit exceeded after #{max_retries} retries"
      raise "AI service temporarily unavailable"
    end

  rescue GeminiAI::NetworkError => e
    retries += 1
    if retries <= max_retries
      Rails.logger.warn "Network error, retrying (attempt #{retries}): #{e.message}"
      sleep(1)
      retry
    else
      Rails.logger.error "Network error after #{max_retries} retries: #{e.message}"
      raise "AI service connection failed"
    end

  rescue GeminiAI::APIError => e
    Rails.logger.error "API error: #{e.message}"
    raise "AI service error: #{e.message}"

  rescue GeminiAI::Error => e
    Rails.logger.error "Gemini AI error: #{e.message}"
    raise "AI service error"
  end
end
```

<br>

# Circuit Breaker Pattern
```ruby
class CircuitBreakerClient
  def initialize(failure_threshold: 5, timeout: 60)
    @client = GeminiAI::Client.new
    @failure_count = 0
    @failure_threshold = failure_threshold
    @timeout = timeout
    @last_failure_time = nil
    @state = :closed  # :closed, :open, :half_open
  end

  def generate_text(prompt, options = {})
    case @state
    when :open
      if Time.now - @last_failure_time > @timeout
        @state = :half_open
      else
        raise "Circuit breaker is open"
      end
    end

    begin
      response = @client.generate_text(prompt, options)

      # Success - reset failure count
      @failure_count = 0
      @state = :closed if @state == :half_open

      response

    rescue GeminiAI::Error => e
      @failure_count += 1
      @last_failure_time = Time.now

      if @failure_count >= @failure_threshold
        @state = :open
      end

      raise e
    end
  end
end
```

<br>

# Prompt Engineering

<br>

# Effective Prompt Structure

<br>

# Clear Instructions
```ruby
# Good - Clear and specific
prompt = "Write a Ruby method that takes an array of integers and returns the sum. Include error handling for non-integer values."

# Bad - Vague
prompt = "Write some Ruby code"
```

<br>

# Context and Examples
```ruby
# Good - Provide context and examples
prompt = <<~PROMPT
  You are a Ruby expert. Write a method to validate email addresses.

  Requirements:
  - Must contain @ symbol
  - Must have domain extension
  - Return true/false

  Example usage:
  validate_email("user@example.com") # => true
  validate_email("invalid-email") # => false
PROMPT

response = client.generate_text(prompt, temperature: 0.3)
```

<br>

# Role-Based Prompts
```ruby
# Technical documentation
tech_prompt = "You are a technical writer. Explain how Ruby blocks work to a beginner programmer."

# Code review
review_prompt = "You are a senior Ruby developer. Review this code for issues and changes: #{code}"

# Creative writing
creative_prompt = "You are a creative writing assistant. Help improve this story opening: #{story_text}"
```

<br>

# Parameter Tuning Guide

<br>

# For Different Use Cases
```ruby
# Factual/Technical Content
factual_params = {
  temperature: 0.1,   # Low creativity
  top_p: 0.8,        # Focused sampling
  top_k: 20,         # Limited vocabulary
  max_tokens: 200    # Concise responses
}

# Creative Content
creative_params = {
  temperature: 0.8,   # High creativity
  top_p: 0.95,       # Diverse sampling
  top_k: 50,         # Full vocabulary
  max_tokens: 400    # Longer responses
}

# Balanced Content
balanced_params = {
  temperature: 0.7,   # Moderate creativity
  top_p: 0.9,        # Good diversity
  top_k: 40,         # Standard vocabulary
  max_tokens: 300    # Medium length
}
```

<br>

# Integration Patterns

<br>

# Rails Application Integration

<br>

# Service Object Pattern
```ruby
# app/services/ai_content_service.rb
class AiContentService
  def initialize
    @client = GeminiAI::Client.new
  end

  def generate_blog_post(topic, style: 'professional')
    prompt = build_blog_prompt(topic, style)

    @client.generate_text(
      prompt,
      temperature: style == 'creative' ? 0.8 : 0.6,
      max_tokens: 800
    )
  rescue GeminiAI::Error => e
    Rails.logger.error "AI Content Service Error: #{e.message}"
    "Unable to generate content at this time."
  end

  private

  def build_blog_prompt(topic, style)
    "Write a #{style} blog post about #{topic}. Include an introduction, main points, and conclusion."
  end
end
```

<br>

# Background Job Integration
```ruby
# app/jobs/content_generation_job.rb
class ContentGenerationJob < ApplicationJob
  queue_as :default

  def perform(user_id, prompt, content_type)
    user = User.find(user_id)
    client = GeminiAI::Client.new

    response = client.generate_text(prompt)

    # Store the generated content
    user.ai_contents.create!(
      prompt: prompt,
      response: response,
      content_type: content_type,
      generated_at: Time.current
    )

    # Notify user
    ContentGeneratedMailer.notify(user, response).deliver_now

  rescue GeminiAI::Error => e
    Rails.logger.error "Content generation failed: #{e.message}"
    # Handle error - maybe retry or notify user
  end
end
```

<br>

# API Wrapper
```ruby
# app/controllers/api/v1/ai_controller.rb
class Api::V1::AiController < ApplicationController
  before_action :authenticate_user!

  def generate
    prompt = params[:prompt]
    options = extract_options(params)

    # Rate limiting per user
    if user_exceeded_rate_limit?
      render json: { error: 'Rate limit exceeded' }, status: 429
      return
    end

    client = GeminiAI::Client.new
    response = client.generate_text(prompt, options)

    # Log usage
    log_ai_usage(current_user, prompt, response)

    render json: { response: response }

  rescue GeminiAI::Error => e
    render json: { error: e.message }, status: 500
  end

  private

  def extract_options(params)
    {
      temperature: params[:temperature]&.to_f || 0.7,
      max_tokens: params[:max_tokens]&.to_i || 300,
      top_p: params[:top_p]&.to_f || 0.9,
      top_k: params[:top_k]&.to_i || 40
    }
  end

  def user_exceeded_rate_limit?
    # Check user's recent requests
    current_user.ai_requests
                .where(created_at: 1.hour.ago..Time.current)
                .count >= 100
  end

  def log_ai_usage(user, prompt, response)
    user.ai_requests.create!(
      prompt: prompt[0..100],  # Store first 100 chars
      response_length: response.length,
      created_at: Time.current
    )
  end
end
```

<br>

# Testing Strategies

<br>

# Unit Testing
```ruby
# spec/services/ai_content_service_spec.rb
RSpec.describe AiContentService do
  let(:service) { described_class.new }

  describe '#generate_blog_post' do
    context 'when API call succeeds' do
      before do
        allow_any_instance_of(GeminiAI::Client).to receive(:generate_text)
          .and_return('Generated blog post content')
      end

      it 'returns generated content' do
        result = service.generate_blog_post('Ruby programming')
        expect(result).to eq('Generated blog post content')
      end
    end

    context 'when API call fails' do
      before do
        allow_any_instance_of(GeminiAI::Client).to receive(:generate_text)
          .and_raise(GeminiAI::APIError.new('API Error'))
      end

      it 'returns fallback message' do
        result = service.generate_blog_post('Ruby programming')
        expect(result).to eq('Unable to generate content at this time.')
      end
    end
  end
end
```

<br>

# Integration Testing
```ruby
# spec/integration/ai_integration_spec.rb
RSpec.describe 'AI Integration', type: :request do
  describe 'POST /api/v1/ai/generate' do
    let(:user) { create(:user) }
    let(:headers) { { 'Authorization' => "Bearer #{user.api_token}" } }

    context 'with valid parameters' do
      it 'generates content successfully' do
        VCR.use_cassette('gemini_api_success') do
          post '/api/v1/ai/generate',
               params: { prompt: 'Write a haiku' },
               headers: headers

          expect(response).to have_http_status(:success)
          expect(JSON.parse(response.body)).to have_key('response')
        end
      end
    end

    context 'with rate limiting' do
      before do
        # Create 100 recent requests for user
        create_list(:ai_request, 100, user: user, created_at: 30.minutes.ago)
      end

      it 'returns rate limit error' do
        post '/api/v1/ai/generate',
             params: { prompt: 'Write a haiku' },
             headers: headers

        expect(response).to have_http_status(:too_many_requests)
      end
    end
  end
end
```

<br>

# Monitoring and Observability

<br>

# Request Logging
```ruby
class LoggedGeminiClient
  def initialize
    @client = GeminiAI::Client.new
  end

  def generate_text(prompt, options = {})
    start_time = Time.now

    Rails.logger.info "Gemini Request Started", {
      prompt_length: prompt.length,
      options: options
    }

    response = @client.generate_text(prompt, options)

    duration = Time.now - start_time

    Rails.logger.info "Gemini Request Completed", {
      duration: duration,
      response_length: response.length,
      success: true
    }

    response

  rescue GeminiAI::Error => e
    duration = Time.now - start_time

    Rails.logger.error "Gemini Request Failed", {
      duration: duration,
      error: e.class.name,
      message: e.message
    }

    raise e
  end
end
```

<br>

# Metrics Collection
```ruby
class MetricsGeminiClient
  def initialize
    @client = GeminiAI::Client.new
    @metrics = {
      requests: 0,
      successes: 0,
      failures: 0,
      total_duration: 0
    }
  end

  def generate_text(prompt, options = {})
    @metrics[:requests] += 1
    start_time = Time.now

    begin
      response = @client.generate_text(prompt, options)
      @metrics[:successes] += 1
      response
    rescue GeminiAI::Error => e
      @metrics[:failures] += 1
      raise e
    ensure
      @metrics[:total_duration] += Time.now - start_time
    end
  end

  def stats
    {
      requests: @metrics[:requests],
      success_rate: @metrics[:requests] > 0 ? @metrics[:successes].to_f / @metrics[:requests] : 0,
      average_duration: @metrics[:requests] > 0 ? @metrics[:total_duration] / @metrics[:requests] : 0
    }
  end
end
```
