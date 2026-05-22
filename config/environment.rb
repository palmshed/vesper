# SPDX-License-Identifier: MIT
# Copyright (c) 2026 vesper

# frozen_string_literal: true

# Environment configuration for GeminiAI gem
require_relative '../lib/gemini'

# Load environment variables from .env file
GeminiAI.load_env

# Configure logging level based on environment
GeminiAI::Utils::Logger.instance.level = case ENV['RAILS_ENV'] || ENV['RACK_ENV'] || 'development'
                                         when 'production'
                                           Logger::ERROR
                                         when 'test'
                                           Logger::WARN
                                         else
                                           Logger::DEBUG
                                         end

# Validate required environment variables
required_vars = ['GEMINI_API_KEY']
missing_vars = required_vars.select { |var| ENV[var].nil? || ENV[var].empty? }

unless missing_vars.empty?
  puts "Warning: Missing required environment variables: #{missing_vars.join(', ')}"
  puts 'Please set them in your .env file or environment'
end
