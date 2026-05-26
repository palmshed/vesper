# SPDX-License-Identifier: MIT
# Copyright (c) 2026 vesper

# frozen_string_literal: true

require 'test_helper'

class ClientEdgeCasesTest < Minitest::Test
  def setup
    @client = GeminiAI::Client.new('AIzaSyDummyTestKeyForUnitTests123456789')
    @test_image = Base64.strict_encode64(File.binread('test/fixtures/test_image.jpg'))
    HTTParty.stubs(:post).returns(Minitest::Test::MockHTTPResponse.new(status: 200,
                                                                       body: '{"candidates":[{"content":{"parts":[{"text":"Test response from Gemini AI"}]}}]}'))
  end

  def test_generate_text_with_long_prompt
    long_prompt = 'a' * 9000
    stub_gemini_request(response: test_response, status: 200)

    error = assert_raises(GeminiAI::Error) do
      @client.generate_text(long_prompt)
    end

    assert_equal 'Prompt too long (max 8192 tokens)', error.message
  end

  def test_generate_image_text_with_empty_image
    error = assert_raises(GeminiAI::Error) do
      @client.generate_image_text('', 'test prompt')
    end

    assert_equal 'Image is required', error.message
  end

  def test_chat_with_system_instruction
    expected_system_instruction = 'You are a helpful assistant'

    # Stub the request with the exact expected format
    stub_request(:post, "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro-latest:generateContent?key=#{@client.instance_variable_get('@api_key')}")
      .with(
        body: {
          contents: [
            { role: 'user', parts: [{ text: 'Hello' }] },
            { role: 'assistant', parts: [{ text: 'Hi there!' }] },
            { role: 'user', parts: [{ text: 'Tell me a joke' }] }
          ],
          systemInstruction: {
            parts: [{ text: expected_system_instruction }]
          },
          generationConfig: {
            temperature: 0.7,
            maxOutputTokens: 1024,
            topP: 0.9,
            topK: 40
          }
        },
        headers: {
          'Accept' => '*/*',
          'Accept-Encoding' => 'gzip;q=1.0,deflate;q=0.6,identity;q=0.3',
          'Content-Type' => 'application/json',
          'User-Agent' => 'Ruby',
          'X-Goog-Api-Client' => 'vesper_ruby_gem/0.1.0'
        }
      )
      .to_return(
        status: 200,
        body: test_response,
        headers: { 'Content-Type': 'application/json' }
      )

    # Call the method with the test data
    messages = [
      { role: 'user', content: 'Hello' },
      { role: 'assistant', content: 'Hi there!' },
      { role: 'user', content: 'Tell me a joke' }
    ]

    result = @client.chat(messages, system_instruction: expected_system_instruction)

    assert_equal 'Test response from Gemini AI', result
  end

  def test_rate_limiting
    stub_gemini_request(response: test_response, status: 200)

    start_time = Time.now
    @client.generate_text('test')
    @client.generate_text('test')
    end_time = Time.now

    # Should take at least 1 second between requests (min_request_interval)
    assert_operator (end_time - start_time), :>=, 1.0
  end

  def test_api_key_masking
    # mask_api_key keeps first 4 and last 4 characters, replaces middle with asterisks
    assert_equal 'AIza*******************************6789',
                 @client.send(:mask_api_key, 'AIzaSyDummyTestKeyForUnitTests123456789')
    assert_equal 'test', @client.send(:mask_api_key, 'test')
    assert_equal '[REDACTED]', @client.send(:mask_api_key, nil)
  end

  private

  def test_response(text = 'Test response from Gemini AI')
    {
      candidates: [
        {
          content: {
            parts: [
              { text: }
            ]
          }
        }
      ]
    }.to_json
  end

  def stub_gemini_request(response: test_response, status: 200)
    api_key = @client.instance_variable_get('@api_key')
    stub_request(:post, /generativelanguage.*key=#{api_key}/)
      .to_return(
        status:,
        body: response,
        headers: { 'Content-Type': 'application/json' }
      )
  end
end
