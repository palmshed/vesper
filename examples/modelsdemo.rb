# SPDX-License-Identifier: MIT
# Copyright (c) 2026 vesper

#!/usr/bin/env ruby
# frozen_string_literal: true

require_relative '../lib/gemini'

# Load environment variables
GeminiAI.load_env

puts 'Gemini AI Ruby Client - New Models Demo'
puts '=' * 50

# Check if API key is available
unless ENV['GEMINI_API_KEY']
  puts 'ERROR: Please set GEMINI_API_KEY environment variable'
  exit 1
end

# Demo prompt
prompt = 'Explain what makes you special in exactly one sentence.'

# Test different models
models_to_demo = [
  { key: :pro, name: 'Gemini 2.5 Pro', description: 'Latest and most capable model' },
  { key: :flash, name: 'Gemini 2.5 Flash', description: 'Fast and efficient latest model' },
  { key: :flash_2_0, name: 'Gemini 2.0 Flash', description: 'Previous generation fast model' },
  { key: :flash_lite, name: 'Gemini 2.0 Flash Lite', description: 'Lightweight model' }
]

models_to_demo.each do |model_info|
  puts "\nTesting #{model_info[:name]}"
  puts "   #{model_info[:description]}"
  puts "   Model ID: #{GeminiAI::Client::MODELS[model_info[:key]]}"
  puts '-' * 40

  begin
    client = GeminiAI::Client.new(model: model_info[:key])

    # Measure response time
    start_time = Time.now
    response = client.generate_text(prompt)
    end_time = Time.now

    response_time = ((end_time - start_time) * 1000).round(2)

    puts "[SUCCESS] Response (#{response_time}ms): #{response.strip}"
  rescue GeminiAI::Error => e
    if e.message.include?('quota')
      puts '[WARNING] Quota exceeded - this is normal for free tier'
    else
      puts "[ERROR] Error: #{e.message}"
    end
  rescue StandardError => e
    puts "[ERROR] Unexpected error: #{e.message}"
  end

  # Small delay to avoid rate limiting
  sleep(1)
end

puts "\n#{'=' * 50}"
puts 'Model Selection Guide:'
puts '* Use :pro (Gemini 2.5 Pro) for complex reasoning and analysis'
puts '* Use :flash (Gemini 2.5 Flash) for fast, general-purpose tasks'
puts '* Use :flash_2_0 (Gemini 2.0 Flash) for compatibility with older workflows'
puts '* Use :flash_lite (Gemini 2.0 Flash Lite) for simple, lightweight tasks'

puts "\nAvailable model keys:"
GeminiAI::Client::MODELS.each do |key, model_id|
  puts "  #{key}: #{model_id}"
end

puts "\nUsage example:"
puts <<~RUBY
  # Use the latest and best model (default)
  client = GeminiAI::Client.new(model: :pro)

  # Use the fastest model
  client = GeminiAI::Client.new(model: :flash)

  # Use a specific version
  client = GeminiAI::Client.new(model: :flash_2_0)
RUBY
