# SPDX-License-Identifier: MIT
# Copyright (c) 2026 vesper

# frozen_string_literal: true

module GeminiAI
  # Base error class for all GeminiAI related errors
  class Error < StandardError; end

  # API related errors
  class APIError < Error; end

  # Authentication errors
  class AuthenticationError < Error; end

  # Rate limit errors
  class RateLimitError < Error; end

  # Invalid request errors
  class InvalidRequestError < Error; end

  # Network/connection errors
  class NetworkError < Error; end
end
