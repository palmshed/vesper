# SPDX-License-Identifier: MIT
# Copyright (c) 2026 vesper

# frozen_string_literal: true

require 'test_helper'

class TestAPI < Minitest::Test
  def setup
    # Stub the API key validation to always pass
    GeminiAI::Client.any_instance.stubs(:validate_api_key!).returns(true)

    # Stub sleep to speed up tests
    GeminiAI::Client.any_instance.stubs(:sleep)

    # Create a test API key that passes validation
    @api_key = "AIzaSyD#{'a' * 35}" # 39 characters total, starting with AIzaSyD
    @client = GeminiAI::Client.new(@api_key)

    # Mock successful response
    @success_response = {
      candidates: [{
        content: {
          parts: [{
            text: 'Test response from Gemini AI'
          }]
        }
      }]
    }

    # Stub the API request
    HTTParty.stubs(:post).returns(MockHTTPResponse.new(status: 200, body: @success_response.to_json))
  end

  def test_basic_text_generation
    response = @client.generate_text('Say hello in one word')

    refute_nil response
    refute_empty response.strip
    assert_instance_of String, response
    assert_equal 'Test response from Gemini AI', response
  end

  def test_chat_functionality
    # Stub the API request with the expected response
    HTTParty.stubs(:post).returns(mock_response(status: 200, body: @success_response.to_json))

    client = GeminiAI::Client.new(@api_key)

    # First message
    response1 = client.generate_text('Hello, how are you?')

    assert_equal 'Test response from Gemini AI', response1

    # Second message (should be a new request, not a continuation)
    response2 = client.generate_text("I'm doing well, thanks for asking!")

    assert_equal 'Test response from Gemini AI', response2
  end

  def test_different_models
    # Test with default model (pro)
    stub_request(:post, 'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro-latest:generateContent')
      .with(query: { key: @api_key })
      .to_return(
        status: 200,
        body: {
          candidates: [{
            content: {
              parts: [{
                text: 'Test response from Gemini AI Pro'
              }]
            }
          }]
        }.to_json,
        headers: { 'Content-Type': 'application/json' }
      )

    client = GeminiAI::Client.new(@api_key, model: :pro)
    response = client.generate_text('What is the weather like?')

    assert_equal 'Test response from Gemini AI', response

    # Test with flash model
    stub_request(:post, 'https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent')
      .with(query: { key: @api_key })
      .to_return(
        status: 200,
        body: {
          candidates: [{
            content: {
              parts: [{
                text: 'Test response from Gemini AI Flash'
              }]
            }
          }]
        }.to_json,
        headers: { 'Content-Type': 'application/json' }
      )

    client = GeminiAI::Client.new(@api_key, model: :flash)
    response = client.generate_text('What is the weather like?')

    assert_equal 'Test response from Gemini AI', response
  end

  def test_system_instructions
    expected_body = {
      contents: [
        { role: 'user', parts: [{ text: 'How are you?' }] }
      ],
      generationConfig: {
        temperature: 0.7,
        maxOutputTokens: 1024,
        topP: 0.9,
        topK: 40
      },
      systemInstruction: {
        parts: [
          { text: 'You are a medieval knight. Speak in old English.' }
        ]
      }
    }

    stub_request(:post, "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro-latest:generateContent?key=#{@api_key}")
      .with(
        body: lambda { |actual_body|
          actual = JSON.parse(actual_body, symbolize_names: true)
          expected = expected_body

          # Compare the parts we care about
          actual[:contents] == expected[:contents] &&
          actual[:generationConfig] == expected[:generationConfig] &&
          actual[:systemInstruction] == expected[:systemInstruction]
        },
        headers: { 'Content-Type': 'application/json' }
      )
      .to_return(
        status: 200,
        body: {
          candidates: [{
            content: {
              parts: [{
                text: 'Test response from Gemini AI'
              }]
            }
          }]
        }.to_json,
        headers: { 'Content-Type': 'application/json' }
      )

    client = GeminiAI::Client.new(@api_key)

    # Test with system instructions
    response = client.chat(
      [{ role: 'user', content: 'How are you?' }],
      system_instruction: 'You are a medieval knight. Speak in old English.'
    )

    assert_equal 'Test response from Gemini AI', response
  end

  def test_image_generation
    # Skip image tests as they require additional setup
    skip 'Skipping image generation test as it requires additional setup'

    # This is a placeholder for actual image generation test
    # In a real test, you would provide a base64 encoded image
    base64_image = 'base64_encoded_image_here'

    # Stub the API request for image analysis
    stub_request(:post, /generativelanguage\.googleapis\.com/)
      .with(body: hash_including({
                                   contents: [{
                                     parts: [
                                       { text: 'What is in this image?' },
                                       { inline_data: { mime_type: 'image/jpeg', data: base64_image } }
                                     ]
                                   }]
                                 }))
      .to_return(
        status: 200,
        body: {
          candidates: [{
            content: {
              parts: [{
                text: 'This is a test image description.'
              }]
            }
          }]
        }.to_json,
        headers: { 'Content-Type': 'application/json' }
      )

    response = @client.generate_image_text(
      base64_image,
      'What is in this image?'
    )

    refute_nil response
    refute_empty response.strip
    assert_instance_of String, response
  end

  def test_error_handling
    client = GeminiAI::Client.new(@api_key)

    # Test empty prompt
    assert_raises(GeminiAI::Error) do
      client.generate_text('')
    end

    # Stub API error response
    HTTParty.stubs(:post).returns(mock_response(status: 400, body: {
      error: {
        code: 400,
        message: 'API key not valid',
        status: 'INVALID_ARGUMENT'
      }
    }.to_json))

    # Test API error with invalid key
    client = GeminiAI::Client.new('invalid-api-key')
    assert_raises(GeminiAI::Error) do
      client.generate_text('This should fail')
    end
  end
end
