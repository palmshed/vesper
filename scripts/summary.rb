#!/usr/bin/env ruby
# frozen_string_literal: true
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 vesper

require_relative '../lib/gemini'

puts 'Vesper status'
puts '=' * 50

# Load environment
GeminiAI.load_env

puts 'Environment loaded'
puts 'Client available'

puts "\nSupported Models:"
GeminiAI::Client::MODELS.each do |key, model_id|
  puts "  #{key.to_s.ljust(12)} -> #{model_id}"
end

puts "\nModel defaults:"
puts '  app    -> gemini-3.5-flash'
puts '  :pro   -> gemini-pro-latest'
puts '  :flash -> gemini-3.5-flash'

puts "\nUsage Examples:"
puts <<~RUBY
  # Ruby client model aliases
  client = GeminiAI::Client.new(model: :pro)    # gemini-pro-latest
  client = GeminiAI::Client.new(model: :flash)  # gemini-3.5-flash

  # Legacy compatibility
  client = GeminiAI::Client.new(model: :flash_2_0)  # Gemini 2.0 Flash
RUBY

puts "\nAvailable Scripts:"
puts '  ruby scripts/modelchecker.rb     - Check model availability'
puts '  ruby examples/modelsdemo.rb      - Demo all models'
puts '  ruby test/runner.rb              - Run Ruby tests'

puts "\nReady."
puts '=' * 50
