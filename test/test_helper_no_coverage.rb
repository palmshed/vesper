# SPDX-License-Identifier: MIT
# Copyright (c) 2026 vesper

# frozen_string_literal: true

# Minimal test helper for CI environments where coverage is not needed
$LOAD_PATH.unshift File.expand_path('../lib', __dir__)
require 'gemini'
require 'minitest/autorun'
# require 'minitest/reporters'
require 'mocha/minitest'
require 'stringio'

# Add helper methods to Minitest::Test
module Minitest
  class Test
    def setup
      @request_body = nil
      HTTParty.stubs(:post).returns do |_url, options|
        @request_body = JSON.parse(options[:body]) if options[:body]
        # Always return image response for now to debug
        MockHTTPResponse.new(status: 200,
                             body: '{"candidates":[{"content":{"parts":[{"text":"A test image description"}]}}]}')
      end
    end

    # Helper method to create a test API key
    def test_api_key
      "AIzaSyD#{'a' * 35}" # 39 characters total, starting with AIzaSyD
    end

    # Helper method to create a test image
    def test_image
      'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=='
    end

    # Helper method to create a test response
    def test_response(text = 'Test response from Gemini AI')
      {
        'candidates' => [{
          'content' => {
            'parts' => [{
              'text' => text
            }]
          }
        }]
      }
    end
  end
end

# Use spec-style reporting
# Minitest::Reporters.use! [Minitest::Reporters::SpecReporter.new]
