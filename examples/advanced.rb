# SPDX-License-Identifier: MIT
# Copyright (c) 2026 vesper

#!/usr/bin/env ruby
# frozen_string_literal: true

require_relative '../lib/gemini'

# Load environment variables
GeminiAI.load_env

# Advanced configuration example
def advanced_configuration
  puts '=== Advanced Configuration ==='

  client = GeminiAI::Client.new

  # Custom parameters for more creative output
  creative_response = client.generate_text(
    'Write a creative story about a robot',
    temperature: 0.9,      # More creative
    max_tokens: 200,       # Longer response
    top_p: 0.95,          # More diverse
    top_k: 50             # Consider more options
  )

  puts "Creative Response: #{creative_response}"

  # Conservative parameters for factual output
  factual_response = client.generate_text(
    'Explain quantum computing',
    temperature: 0.1,      # More deterministic
    max_tokens: 100,       # Shorter response
    top_p: 0.8,           # Less diverse
    top_k: 20             # Consider fewer options
  )

  puts "\nFactual Response: #{factual_response}"
end

# Error handling example
def error_handling_example
  puts "\n=== Error Handling Example ==="

  begin
    # This will fail - empty prompt
    client = GeminiAI::Client.new
    client.generate_text('')
  rescue GeminiAI::Error => e
    puts "Caught expected error: #{e.message}"
  end

  begin
    # This will fail - invalid API key
    invalid_client = GeminiAI::Client.new('invalid_key')
    invalid_client.generate_text('Hello')
  rescue GeminiAI::Error => e
    puts "Caught API key error: #{e.message}"
  end
end

# Batch processing example
def batch_processing
  puts "\n=== Batch Processing Example ==="

  client = GeminiAI::Client.new
  prompts = [
    'Write a haiku about coding',
    'Explain recursion briefly',
    'What is the best programming language?'
  ]

  prompts.each_with_index do |prompt, index|
    response = client.generate_text(prompt)
    puts "#{index + 1}. #{prompt}"
    puts "   Response: #{response}\n\n"
  rescue StandardError => e
    puts "#{index + 1}. Error processing '#{prompt}': #{e.message}\n\n"
  end
end

# Run advanced examples
begin
  advanced_configuration
  error_handling_example
  batch_processing
rescue StandardError => e
  puts "Unexpected Error: #{e.message}"
end
