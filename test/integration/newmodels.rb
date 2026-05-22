# SPDX-License-Identifier: MIT
# Copyright (c) 2026 vesper

# frozen_string_literal: true

require 'test_helper'

# Module to encapsulate common test logic for model testing
module ModelTestHelper
  def setup_model_test
    # Stub the API key validation to always pass
    GeminiAI::Client.any_instance.stubs(:validate_api_key!).returns(true)
    GeminiAI::Client.any_instance.stubs(:sleep)
  end

  def test_model(model_name, model_id)
    expected_body = build_expected_request_body
    stub_model_request(model_id, expected_body)
    client, response = make_model_request(model_name)
    verify_model_response(response, model_id, client)
  end

  def test_model_comparison(models, prompt: 'What is 2+2? Answer in one word.')
    responses = {}

    models.each do |model_name|
      client = GeminiAI::Client.new(test_api_key, model: model_name, debug: true)
      stub_model_comparison_request(model_name)
      responses[model_name] = client.generate_text(prompt)

      assert_equal model_name, client.instance_variable_get(:@model).to_sym
    end

    verify_responses(responses, models)
  end

  private

  def build_expected_request_body
    {
      contents: [{
        parts: [{ text: 'Test prompt' }]
      }],
      generationConfig: {
        temperature: 0.7,
        maxOutputTokens: 1024,
        topP: 0.9,
        topK: 40
      }
    }
  end

  def stub_model_request(model_id, expected_body)
    stub_gemini_request(
      model: model_id,
      with_body: expected_body,
      response: {
        candidates: [{
          content: {
            parts: [{
              text: 'Test response from Gemini AI'
            }]
          }
        }]
      }
    )
  end

  def make_model_request(model_name)
    client = create_test_client(model: model_name)
    response = client.generate_text('Test prompt')
    [client, response]
  end

  def verify_model_response(response, model_id, client)
    refute_nil response
    refute_empty response.strip
    assert_instance_of String, response
    assert_equal 'Test response from Gemini AI', response
    assert_equal model_id, client.instance_variable_get(:@model)
  end

  def stub_model_comparison_request(model_name)
    stub_request(:post, /generativelanguage\.googleapis\.com/)
      .to_return(
        status: 200,
        body: {
          candidates: [{
            content: {
              parts: [{
                text: "Response from #{model_name}"
              }]
            }
          }]
        }.to_json,
        headers: { 'Content-Type' => 'application/json' }
      )
  end

  def verify_responses(responses, models)
    assert_equal models.size, responses.size
    assert_equal models.size, responses.values.uniq.size

    models.each do |model|
      assert_includes responses[model], "Response from #{model}"
    end
  end
end
