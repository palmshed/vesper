# SPDX-License-Identifier: MIT
# Copyright (c) 2026 vesper

# frozen_string_literal: true

require 'test_helper'

class GeminiTest < Minitest::Test
  def setup
    @original_env = ENV.to_h.dup
    ENV.delete('GEMINI_API_KEY')
  end

  def teardown
    ENV.clear
    ENV.update(@original_env)
  end

  def test_new_client_creation
    # Use a valid API key format that will pass validation
    valid_api_key = 'AIzaSyDummyTestKeyForUnitTests123456789'
    client = GeminiAI.new(valid_api_key)

    assert_instance_of GeminiAI::Client, client
  end

  def test_new_client_with_options
    # Use a valid API key format that will pass validation
    valid_api_key = 'AIzaSyDummyTestKeyForUnitTests123456789'
    client = GeminiAI.new(valid_api_key, model: :flash)

    assert_instance_of GeminiAI::Client, client
    assert_equal 'gemini-2.5-flash', client.instance_variable_get(:@model)
  end

  def test_load_env
    # Create a temporary .env file
    temp_env = Tempfile.new('.env')
    temp_env.write("TEST_KEY=test_value\nANOTHER_KEY=123")
    temp_env.close

    # Test loading the .env file
    GeminiAI.load_env(temp_env.path)

    # Check that environment variables were set
    assert_equal 'test_value', ENV.fetch('TEST_KEY', nil)
    assert_equal '123', ENV.fetch('ANOTHER_KEY', nil)
  ensure
    temp_env&.unlink
  end
end
