# SPDX-License-Identifier: MIT
# Copyright (c) 2026 vesper

#!/usr/bin/env ruby
# frozen_string_literal: true

require_relative '../lib/gemini'

# Load environment variables
GeminiAI.load_env

puts 'Models demo'
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
  { key: :pro, name: 'Pro', description: 'Default model' },
  { key: :flash, name: 'Flash', description: 'Fast general-purpose model' },
  { key: :pro_3_1_preview, name: 'Gemini 3.1 Pro Preview', description: 'Preview Pro model' },
  { key: :flash_3_1_lite, name: 'Gemini 3.1 Flash Lite', description: 'Lightweight text model' },
  { key: :flash_2_0, name: 'Gemini 2.0 Flash', description: 'Pinned 2.0 model' }
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
puts '* Use :pro for the default Pro alias'
puts '* Use :flash for fast, general-purpose tasks'
puts '* Use :flash_3_1_lite for lighter requests'
puts '* Use :flash_2_0 when that exact model is required'

puts "\nAvailable model keys:"
GeminiAI::Client::MODELS.each do |key, model_id|
  puts "  #{key}: #{model_id}"
end

puts "\nUsage example:"
puts <<~RUBY
  # Use the default model
  client = GeminiAI::Client.new(model: :pro)

  # Use the fastest model
  client = GeminiAI::Client.new(model: :flash)

  # Use a specific version
  client = GeminiAI::Client.new(model: :flash_2_0)
RUBY
