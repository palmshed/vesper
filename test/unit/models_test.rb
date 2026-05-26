# SPDX-License-Identifier: MIT
# Copyright (c) 2026 vesper

# frozen_string_literal: true

require 'test_helper'

class TestModels < Minitest::Test
  def setup
    # Use a mock API key for testing
    @api_key = 'AIzaSyDummyTestKeyForUnitTests123456789'
  end

  def test_default_pro_model
    client = GeminiAI::Client.new(@api_key, model: :pro)

    assert_instance_of GeminiAI::Client, client
    assert_equal 'gemini-pro-latest', client.instance_variable_get(:@model)
  end

  def test_default_flash_model
    client = GeminiAI::Client.new(@api_key, model: :flash)

    assert_instance_of GeminiAI::Client, client
    assert_equal 'gemini-3.5-flash', client.instance_variable_get(:@model)
  end

  def test_generate_content_text_models
    expected_models = {
      flash_latest: 'gemini-flash-latest',
      pro_latest: 'gemini-pro-latest',
      flash_3_5: 'gemini-3.5-flash',
      pro_3_preview: 'gemini-3-pro-preview',
      flash_3_preview: 'gemini-3-flash-preview',
      pro_3_1_preview: 'gemini-3.1-pro-preview',
      flash_3_1_lite: 'gemini-3.1-flash-lite',
      pro_2_5: 'gemini-2.5-pro',
      flash_2_5: 'gemini-2.5-flash',
      flash_2_0: 'gemini-2.0-flash'
    }

    expected_models.each do |key, model_id|
      client = GeminiAI::Client.new(@api_key, model: key)

      assert_equal model_id, client.instance_variable_get(:@model)
    end
  end

  def test_short_aliases
    flash_2_0_client = GeminiAI::Client.new(@api_key, model: :flash_2_0)
    lite_client = GeminiAI::Client.new(@api_key, model: :flash_lite)
    pro_2_0_client = GeminiAI::Client.new(@api_key, model: :pro_2_0)

    assert_equal 'gemini-2.0-flash', flash_2_0_client.instance_variable_get(:@model)
    assert_equal 'gemini-3.1-flash-lite', lite_client.instance_variable_get(:@model)
    assert_equal 'gemini-2.0-flash', pro_2_0_client.instance_variable_get(:@model)
  end

  def test_all_supported_models
    GeminiAI::Client::MODELS.each do |model_key, model_id|
      client = GeminiAI::Client.new(@api_key, model: model_key)

      assert_instance_of GeminiAI::Client, client, "Failed to create client for model: #{model_key} (#{model_id})"
    end
  end

  def test_invalid_model_defaults_to_pro
    client = GeminiAI::Client.new(@api_key, model: :invalid_model)

    assert_instance_of GeminiAI::Client, client
    assert_equal 'gemini-pro-latest', client.instance_variable_get(:@model)
  end
end
