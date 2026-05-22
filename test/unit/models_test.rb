# SPDX-License-Identifier: MIT
# Copyright (c) 2026 vesper

# frozen_string_literal: true

require 'test_helper'

class TestModels < Minitest::Test
  def setup
    # Use a mock API key for testing
    @api_key = 'AIzaSyDummyTestKeyForUnitTests123456789'
  end

  def test_gemini_2_5_pro_model
    client = GeminiAI::Client.new(@api_key, model: :pro)

    assert_instance_of GeminiAI::Client, client
    # Should use gemini-2.5-pro by default now
  end

  def test_gemini_2_5_flash_model
    client = GeminiAI::Client.new(@api_key, model: :flash)

    assert_instance_of GeminiAI::Client, client
    # Should use gemini-2.5-flash by default now
  end

  def test_gemini_2_0_models
    flash_2_0_client = GeminiAI::Client.new(@api_key, model: :flash_2_0)
    pro_2_0_client = GeminiAI::Client.new(@api_key, model: :pro_2_0)
    lite_client = GeminiAI::Client.new(@api_key, model: :flash_lite)

    assert_instance_of GeminiAI::Client, flash_2_0_client
    assert_instance_of GeminiAI::Client, pro_2_0_client
    assert_instance_of GeminiAI::Client, lite_client
  end

  def test_all_supported_models
    GeminiAI::Client::MODELS.each do |model_key, model_id|
      client = GeminiAI::Client.new(@api_key, model: model_key)

      assert_instance_of GeminiAI::Client, client, "Failed to create client for model: #{model_key} (#{model_id})"
    end
  end

  def test_invalid_model_defaults_to_pro
    # Should not raise error, should default to pro model (now gemini-2.5-pro)
    client = GeminiAI::Client.new(@api_key, model: :invalid_model)

    assert_instance_of GeminiAI::Client, client
  end
end
