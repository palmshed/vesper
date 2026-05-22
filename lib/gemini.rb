# SPDX-License-Identifier: MIT
# Copyright (c) 2026 vesper

# frozen_string_literal: true

# Main entry point for the GeminiAI gem
require_relative 'core/version'
require_relative 'core/errors'
require_relative 'core/client'
require_relative 'utils/loader'
require_relative 'utils/logger'

module GeminiAI
  # Convenience method to create a new client
  def self.new(api_key = nil, model: :pro)
    Client.new(api_key, model: model)
  end

  # Load environment variables
  def self.load_env(file_path = '.env')
    Utils::Loader.load(file_path)
  end
end
