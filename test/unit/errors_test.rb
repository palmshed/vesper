# SPDX-License-Identifier: MIT
# Copyright (c) 2026 vesper

# frozen_string_literal: true

require 'test_helper'

class ErrorsTest < Minitest::Test
  def test_error_inheritance
    assert_kind_of StandardError, GeminiAI::Error.new
  end

  def test_api_error_inheritance
    assert_kind_of GeminiAI::Error, GeminiAI::APIError.new
  end

  def test_authentication_error_inheritance
    assert_kind_of GeminiAI::Error, GeminiAI::AuthenticationError.new
  end

  def test_rate_limit_error_inheritance
    assert_kind_of GeminiAI::Error, GeminiAI::RateLimitError.new
  end

  def test_invalid_request_error_inheritance
    assert_kind_of GeminiAI::Error, GeminiAI::InvalidRequestError.new
  end

  def test_network_error_inheritance
    assert_kind_of GeminiAI::Error, GeminiAI::NetworkError.new
  end

  def test_error_message
    message = 'Test error message'

    assert_equal message, GeminiAI::Error.new(message).message
  end

  def test_api_error_message
    message = 'Test error message'

    assert_equal message, GeminiAI::APIError.new(message).message
  end

  def test_authentication_error_message
    message = 'Test error message'

    assert_equal message, GeminiAI::AuthenticationError.new(message).message
  end

  def test_rate_limit_error_message
    message = 'Test error message'

    assert_equal message, GeminiAI::RateLimitError.new(message).message
  end

  def test_invalid_request_error_message
    message = 'Test error message'

    assert_equal message, GeminiAI::InvalidRequestError.new(message).message
  end

  def test_network_error_message
    message = 'Test error message'

    assert_equal message, GeminiAI::NetworkError.new(message).message
  end
end
