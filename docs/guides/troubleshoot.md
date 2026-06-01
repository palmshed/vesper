# Troubleshooting

<br>

Common issues and solutions when using Vesper.

<br>

# API Key Issues

<br>

# "API key is required"

<br>

**Problem**: The client cannot find your API key.

<br>

**Solutions**:
1. **Check environment variable**:
   ```bash
   echo $GEMINI_API_KEY
   ```

<br>

2. **Set environment variable**:
   ```bash
   export GEMINI_API_KEY="your_api_key_here"
   ```

<br>

3. **Use .env file**:
   ```bash
   echo "GEMINI_API_KEY=your_api_key_here" > .env
   ```

<br>

   Then in your Ruby code:
   ```ruby
   GeminiAI.load_env
   client = GeminiAI::Client.new
   ```

<br>

4. **Pass API key directly** (avoid in production):
   ```ruby
   client = GeminiAI::Client.new('your_api_key_here')
   ```

<br>

# "Invalid API key format"

<br>

**Problem**: Your API key doesn't match the expected format.

<br>

**Symptoms**:
- API key doesn't start with "AIza"
- Extra spaces or characters in the key
- Truncated or incomplete key

<br>

**Solutions**:
1. **Verify API key format**:
   ```ruby
   api_key = ENV['GEMINI_API_KEY']
   puts "Key starts with AIza: #{api_key.start_with?('AIza')}"
   puts "Key length: #{api_key.length}"
   ```

<br>

2. **Get a new API key**:
   - Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
   - Create a new API key
   - Copy the complete key

<br>

3. **Check for hidden characters**:
   ```bash
   # Show hidden characters
   cat -A .env
   ```

<br>

# "Authentication failed"

<br>

**Problem**: API key is invalid or expired.

<br>

**Solutions**:
1. **Test API key manually**:
   ```bash
   curl -H "Content-Type: application/json" \
        -d '{"contents":[{"parts":[{"text":"Hello"}]}]}' \
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key=YOUR_API_KEY"
   ```

<br>

2. **Generate new API key**:
   - Old keys may expire or be revoked
   - Create a fresh key in Google AI Studio

<br>

3. **Check API key permissions**:
   - Ensure the key has access to Gemini models
   - Verify billing is set up if required

<br>

# Network Issues

<br>

# "Connection timeout"

<br>

**Problem**: Network requests are timing out.

<br>

**Solutions**:
1. **Check internet connection**:
   ```bash
   ping google.com
   ```

<br>

2. **Test API endpoint**:
   ```bash
   curl -I https://generativelanguage.googleapis.com
   ```

<br>

3. **Check firewall/proxy settings**:
   - Corporate firewalls may block API requests
   - Configure proxy if needed

<br>

4. **Increase timeout** (if using custom HTTP client):
   ```ruby
   # The gem uses 30-second timeout by default
   # This is usually sufficient
   ```

<br>

# "SSL certificate verification failed"

<br>

**Problem**: SSL/TLS certificate issues.

<br>

**Solutions**:
1. **Update system certificates**:
   ```bash
   # macOS
   brew install ca-certificates

   # Ubuntu/Debian
   sudo apt-get update && sudo apt-get install ca-certificates
   ```

<br>

2. **Check Ruby SSL setup**:
   ```ruby
   require 'openssl'
   puts OpenSSL::X509::DEFAULT_CERT_FILE
   puts OpenSSL::X509::DEFAULT_CERT_DIR
   ```

<br>

# Rate Limiting

<br>

# "Rate limit exceeded"

<br>

**Problem**: Too many requests in a short time period.

<br>

Limits depend on your key, billing state, region, and selected model.

<br>

**Solutions**:
1. **Let the client retry**:
   The client retries HTTP 429 responses three times with exponential backoff.

<br>

2. **Add delays between requests**:
   ```ruby
   prompts.each do |prompt|
     response = client.generate_text(prompt)
     sleep(1)
   end
   ```

<br>

3. **Handle final failure**:
   ```ruby
   begin
     response = client.generate_text(prompt)
   rescue GeminiAI::Error => e
     if e.message.include?('Rate limit exceeded')
       warn 'Rate limit exceeded. Wait and retry later.'
     else
       raise e
     end
   end
   ```

<br>

4. **Use smaller batches**:
   ```ruby
   prompts.each_slice(10) do |batch|
     batch.each { |prompt| client.generate_text(prompt) }
     sleep(60)
   end
   ```

<br>

# Request Issues

<br>

# "Prompt cannot be empty"

<br>

**Problem**: Empty or nil prompt passed to generate_text.

<br>

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

<br>

2. **Provide default prompts**:
   ```ruby
   prompt = user_input.to_s.strip
   prompt = "Respond to the request." if prompt.empty?
   response = client.generate_text(prompt)
   ```

<br>

# "Prompt too long"

<br>

**Problem**: Prompt exceeds the client guard of 8192 characters.

<br>

**Solutions**:
1. **Check prompt length**:
   ```ruby
   puts "Prompt characters: #{prompt.length}"
   ```

<br>

2. **Truncate long prompts**:
   ```ruby
   MAX_PROMPT_LENGTH = 8192

   if prompt.length > MAX_PROMPT_LENGTH
     prompt = prompt[0...MAX_PROMPT_LENGTH]
   end
   ```

<br>

3. **Split large documents**:
   ```ruby
   def process_large_document(document)
     chunks = document.scan(/.{1,2000}/)

     chunks.map do |chunk|
       client.generate_text("Summarize this text: #{chunk}")
     end
   end
   ```

<br>

# Response Issues

<br>

# "Empty response"

<br>

**Problem**: API returns empty or nil response.

<br>

**Solutions**:
1. **Check response handling**:
   ```ruby
   response = client.generate_text(prompt)

   if response.nil? || response.strip.empty?
     puts "Warning: Empty response received"
     response = "No response generated"
   end
   ```

<br>

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

<br>

# "Unexpected response format"

<br>

**Problem**: Response doesn't match expected format.

<br>

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

<br>

2. **Handle JSON responses** (if expecting structured data):
   ```ruby
   begin
     parsed = JSON.parse(response)
   rescue JSON::ParserError
     puts "Response is not valid JSON: #{response}"
   end
   ```

<br>

# CLI Issues

<br>

# "Permission denied" when running CLI

<br>

**Problem**: CLI script is not executable.

<br>

**Solution**:
```bash
chmod +x bin/gemini
```

<br>

# "Command not found"

<br>

**Problem**: CLI script path issues.

<br>

**Solutions**:
1. **Run from project root**:
   ```bash
   ./bin/gemini test
   ```

<br>

2. **Check file exists**:
   ```bash
   ls -la bin/gemini
   ```

<br>

3. **Check shebang line**:
   ```bash
   head -1 bin/gemini
   # Should show: #!/usr/bin/env ruby
   ```

<br>

# Installation Issues

<br>

# "Gem not found"

<br>

**Problem**: Gem installation or loading issues.

<br>

**Solutions**:
1. **Install gem**:
   ```bash
   gem install friday_gemini_ai
   ```

<br>

2. **Check gem path**:
   ```bash
   gem which vesper
   ```

<br>

3. **Use bundle if using Gemfile**:
   ```bash
   bundle install
   bundle exec ruby your_script.rb
   ```

<br>

# "Ruby version compatibility"

<br>

**Problem**: Ruby version too old.

<br>

**Requirements**: Ruby 3.3 or higher

<br>

**Solutions**:
1. **Check Ruby version**:
   ```bash
   ruby --version
   ```

<br>

2. **Update Ruby** (using rbenv):
   ```bash
   rbenv install 3.3.11
   rbenv global 3.3.11
   ```

<br>

3. **Update Ruby** (using RVM):
   ```bash
   rvm install 3.3.11
   rvm use 3.3.11 --default
   ```

<br>

# Debugging

<br>

# Enable Debug Logging

<br>

```ruby
require 'logger'

GeminiAI::Client.logger.level = Logger::DEBUG

client = GeminiAI::Client.new
response = client.generate_text("Test prompt")
```

<br>

# Test API Connection

<br>

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

<br>

# Inspect Request Details

<br>

```ruby
require 'logger'

GeminiAI::Client.logger.level = Logger::DEBUG
client = GeminiAI::Client.new
response = client.generate_text("Test")

# Debug logs include:
# - Request URL
# - Request body
# - Response status
# - Response body
```

<br>

# Getting Help

<br>

# Check Logs

<br>

Look for detailed error messages in your application logs:
```ruby
Rails.logger.error "Gemini AI Error: #{e.message}"
```

<br>

# Test with CLI

<br>

Use the CLI to isolate issues:
```bash
# Test basic connection
./bin/gemini test

# Test with specific prompt
./bin/gemini generate "Simple test prompt"
```

<br>

# Minimal Reproduction

<br>

Create a minimal script to reproduce the issue:
```ruby
#!/usr/bin/env ruby

require 'vesper'

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

<br>

# Common Error Patterns

<br>

1. **Authentication errors** → Check API key
2. **Network errors** → Check connectivity
3. **Rate limit errors** → Add delays/retry logic
4. **Empty responses** → Check prompt and parameters
5. **Installation errors** → Check Ruby version and dependencies

<br>

If you're still having issues after trying these solutions, please check the project's GitHub issues or create a new issue with:
- Ruby version
- Gem version
- Full error message
- Minimal code to reproduce the problem
