# Troubleshooting

Common issues and solutions when using Vesper.

## API Key Issues

### "API key is required"

**Problem**: The client cannot find your API key.

**Solutions**:
1. **Check environment variable**:
   ```bash
   echo $GEMINI_API_KEY
   ```

2. **Set environment variable**:
   ```bash
   export GEMINI_API_KEY="your_api_key_here"
   ```

3. **Use .env file**:
   ```bash
   echo "GEMINI_API_KEY=your_api_key_here" > .env
   ```

   Then in your Ruby code:
   ```ruby
   GeminiAI.load_env
   client = GeminiAI::Client.new
   ```

4. **Pass API key directly** (not recommended for production):
   ```ruby
   client = GeminiAI::Client.new('your_api_key_here')
   ```

### "Invalid API key format"

**Problem**: Your API key doesn't match the expected format.

**Symptoms**:
- API key doesn't start with "AIza"
- Extra spaces or characters in the key
- Truncated or incomplete key

**Solutions**:
1. **Verify API key format**:
   ```ruby
   api_key = ENV['GEMINI_API_KEY']
   puts "Key starts with AIza: #{api_key.start_with?('AIza')}"
   puts "Key length: #{api_key.length}"
   ```

2. **Get a new API key**:
   - Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
   - Create a new API key
   - Copy the complete key

3. **Check for hidden characters**:
   ```bash
   # Show hidden characters
   cat -A .env
   ```

### "Authentication failed"

**Problem**: API key is invalid or expired.

**Solutions**:
1. **Test API key manually**:
   ```bash
   curl -H "Content-Type: application/json" \
        -d '{"contents":[{"parts":[{"text":"Hello"}]}]}' \
        "https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key=YOUR_API_KEY"
   ```

2. **Generate new API key**:
   - Old keys may expire or be revoked
   - Create a fresh key in Google AI Studio

3. **Check API key permissions**:
   - Ensure the key has access to Gemini models
   - Verify billing is set up if required

## Network Issues

### "Connection timeout"

**Problem**: Network requests are timing out.

**Solutions**:
1. **Check internet connection**:
   ```bash
   ping google.com
   ```

2. **Test API endpoint**:
   ```bash
   curl -I https://generativelanguage.googleapis.com
   ```

3. **Check firewall/proxy settings**:
   - Corporate firewalls may block API requests
   - Configure proxy if needed

4. **Increase timeout** (if using custom HTTP client):
   ```ruby
   # The gem uses 30-second timeout by default
   # This is usually sufficient
   ```

### "SSL certificate verification failed"

**Problem**: SSL/TLS certificate issues.

**Solutions**:
1. **Update system certificates**:
   ```bash
   # macOS
   brew install ca-certificates

   # Ubuntu/Debian
   sudo apt-get update && sudo apt-get install ca-certificates
   ```

2. **Check Ruby SSL setup**:
   ```ruby
   require 'openssl'
   puts OpenSSL::X509::DEFAULT_CERT_FILE
   puts OpenSSL::X509::DEFAULT_CERT_DIR
   ```

## Rate Limiting

### "Rate limit exceeded"

**Problem**: Too many requests in a short time period.

**Current Limits**:
- 60 requests per minute
- 32,000 tokens per minute
- 1,500 requests per day

**Solutions**:
1. **Implement exponential backoff**:
   ```ruby
   def generate_with_retry(prompt, max_retries: 3)
     retries = 0
     begin
       client.generate_text(prompt)
     rescue GeminiAI::RateLimitError => e
       retries += 1
       if retries <= max_retries
         wait_time = 2 ** retries
         sleep(wait_time)
         retry
       else
         raise e
       end
     end
   end
   ```

2. **Add delays between requests**:
   ```ruby
   prompts.each do |prompt|
     response = client.generate_text(prompt)
     sleep(1)  # Wait 1 second between requests
   end
   ```

3. **Use batch processing**:
   ```ruby
   # Process in smaller batches
   prompts.each_slice(10) do |batch|
     batch.each { |prompt| client.generate_text(prompt) }
     sleep(60)  # Wait 1 minute between batches
   end
   ```

## Request Issues

### "Prompt cannot be empty"

**Problem**: Empty or nil prompt passed to generate_text.

**Solutions**:
1. **Validate input**:
   ```ruby
   def safe_generate(prompt)
     if prompt.nil? || prompt.strip.empty?
       raise ArgumentError, "Prompt cannot be empty"
     end

     client.generate_text(prompt)
   end
   ```

2. **Provide default prompts**:
   ```ruby
   prompt = user_input.presence || "Please provide a helpful response."
   response = client.generate_text(prompt)
   ```

### "Request too large"

**Problem**: Prompt exceeds maximum token limit.

**Solutions**:
1. **Check prompt length**:
   ```ruby
   # Rough token estimation: 1 token ≈ 4 characters
   estimated_tokens = prompt.length / 4
   puts "Estimated tokens: #{estimated_tokens}"
   ```

2. **Truncate long prompts**:
   ```ruby
   MAX_PROMPT_LENGTH = 8000  # Conservative limit

   if prompt.length > MAX_PROMPT_LENGTH
     prompt = prompt[0..MAX_PROMPT_LENGTH] + "..."
   end
   ```

3. **Split large documents**:
   ```ruby
   def process_large_document(document)
     chunks = document.scan(/.{1,2000}/)

     chunks.map do |chunk|
       client.generate_text("Summarize this text: #{chunk}")
     end
   end
   ```

## Response Issues

### "Empty response"

**Problem**: API returns empty or nil response.

**Solutions**:
1. **Check response handling**:
   ```ruby
   response = client.generate_text(prompt)

   if response.nil? || response.strip.empty?
     puts "Warning: Empty response received"
     response = "No response generated"
   end
   ```

2. **Adjust generation parameters**:
   ```ruby
   # Try different parameters
   response = client.generate_text(
     prompt,
     temperature: 0.7,
     max_tokens: 100,
     top_p: 0.9
   )
   ```

### "Unexpected response format"

**Problem**: Response doesn't match expected format.

**Solutions**:
1. **Add response validation**:
   ```ruby
   def validate_response(response)
     unless response.is_a?(String)
       raise "Expected string response, got #{response.class}"
     end

     if response.length < 10
       puts "Warning: Very short response: #{response}"
     end

     response
   end
   ```

2. **Handle JSON responses** (if expecting structured data):
   ```ruby
   begin
     parsed = JSON.parse(response)
   rescue JSON::ParserError
     puts "Response is not valid JSON: #{response}"
   end
   ```

## CLI Issues

### "Permission denied" when running CLI

**Problem**: CLI script is not executable.

**Solution**:
```bash
chmod +x bin/gemini
```

### "Command not found"

**Problem**: CLI script path issues.

**Solutions**:
1. **Run from project root**:
   ```bash
   ./bin/gemini test
   ```

2. **Check file exists**:
   ```bash
   ls -la bin/gemini
   ```

3. **Check shebang line**:
   ```bash
   head -1 bin/gemini
   # Should show: #!/usr/bin/env ruby
   ```

## Installation Issues

### "Gem not found"

**Problem**: Gem installation or loading issues.

**Solutions**:
1. **Install gem**:
   ```bash
   gem install friday_gemini_ai
   ```

2. **Check gem path**:
   ```bash
   gem which vesper
   ```

3. **Use bundle if using Gemfile**:
   ```bash
   bundle install
   bundle exec ruby your_script.rb
   ```

### "Ruby version compatibility"

**Problem**: Ruby version too old.

**Requirements**: Ruby 3.1 or higher

**Solutions**:
1. **Check Ruby version**:
   ```bash
   ruby --version
   ```

2. **Update Ruby** (using rbenv):
   ```bash
   rbenv install 3.1.0
   rbenv global 3.1.0
   ```

3. **Update Ruby** (using RVM):
   ```bash
   rvm install 3.1.0
   rvm use 3.1.0 --default
   ```

## Debugging

### Enable Debug Logging

```ruby
# Enable debug logging to see detailed request/response info
require 'logger'

# Set debug level
GeminiAI::Utils::Logger.instance.level = Logger::DEBUG

# Now all requests will show detailed information
client = GeminiAI::Client.new
response = client.generate_text("Test prompt")
```

### Test API Connection

```ruby
# Test basic connectivity
begin
  client = GeminiAI::Client.new
  response = client.generate_text("Say 'Connection successful!'")
  puts "[SUCCESS] API connection working: #{response}"
rescue GeminiAI::Error => e
  puts "[ERROR] API connection failed: #{e.message}"
end
```

### Inspect Request Details

```ruby
# Enable debug mode to see full request/response
ENV['DEBUG'] = 'true'

client = GeminiAI::Client.new
response = client.generate_text("Test")

# This will show:
# - Request URL
# - Request headers
# - Request body
# - Response status
# - Response body
```

## Getting Help

### Check Logs

Look for detailed error messages in your application logs:
```ruby
Rails.logger.error "Gemini AI Error: #{e.message}"
```

### Test with CLI

Use the CLI to isolate issues:
```bash
# Test basic connection
./bin/gemini test

# Test with specific prompt
./bin/gemini generate "Simple test prompt"
```

### Minimal Reproduction

Create a minimal script to reproduce the issue:
```ruby
#!/usr/bin/env ruby

require_relative 'src/gemini'

begin
  GeminiAI.load_env
  client = GeminiAI::Client.new
  response = client.generate_text("Hello")
  puts "Success: #{response}"
rescue => e
  puts "Error: #{e.class} - #{e.message}"
  puts e.backtrace.first(5)
end
```

### Common Error Patterns

1. **Authentication errors** → Check API key
2. **Network errors** → Check connectivity
3. **Rate limit errors** → Add delays/retry logic
4. **Empty responses** → Check prompt and parameters
5. **Installation errors** → Check Ruby version and dependencies

If you're still having issues after trying these solutions, please check the project's GitHub issues or create a new issue with:
- Ruby version
- Gem version
- Full error message
- Minimal code to reproduce the problem
