# frozen_string_literal: true
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 vesper

require 'httparty'
require 'json'
require 'base64'
require 'logger'
require 'dotenv/load'
require_relative 'errors'
require_relative '../utils/moderation'

module GeminiAI
  # Core client class for Gemini AI API communication
  class Client
    BASE_URL = 'https://generativelanguage.googleapis.com/v1/models'
    # Model mappings
    # Current supported models
    MODELS = {
      # Gemini 2.5 models (latest)
      pro: 'gemini-2.5-pro',
      flash: 'gemini-2.5-flash',

      # Gemini 2.0 models
      flash_2_0: 'gemini-2.0-flash',
      flash_lite: 'gemini-2.0-flash-lite',

      # Legacy aliases for backward compatibility
      pro_2_0: 'gemini-2.0-flash'
    }.freeze

    # Deprecated models removed in this version (log warning and default to :pro)
    DEPRECATED_MODELS = {
      pro_1_5: 'gemini-1.5-pro',
      flash_1_5: 'gemini-1.5-flash',
      flash_8b: 'gemini-1.5-flash-8b'
    }.freeze

    # Configure logging
    def self.logger
      @logger ||= Logger.new($stdout).tap do |log|
        log.level = Logger::DEBUG
        log.formatter = proc do |severity, datetime, _progname, msg|
          # Mask any potential API key in logs
          masked_msg = msg.to_s.gsub(/AIza[a-zA-Z0-9_-]{35,}/, '[REDACTED]')
          "#{datetime}: #{severity} -- #{masked_msg}\n"
        end
      end
    end

    def initialize(api_key = nil, model: :pro)
      # Prioritize passed API key, then environment variable
      @api_key = api_key || ENV.fetch('GEMINI_API_KEY', nil)

      # Rate limiting - track last request time
      @last_request_time = nil
      # More conservative rate limiting in CI environments
      @min_request_interval = ENV['CI'] == 'true' || ENV['GITHUB_ACTIONS'] == 'true' ? 3.0 : 1.0

      # Extensive logging for debugging
      self.class.logger.debug('Initializing Client')
      self.class.logger.debug("API Key present: #{!@api_key.nil?}")
      self.class.logger.debug("API Key length: #{@api_key&.length}")

      # Validate API key before proceeding
      validate_api_key!

      @model = resolve_model(model)

      self.class.logger.debug("Selected model: #{@model}")
    end

    def generate_text(prompt, options = {})
      validate_prompt!(prompt)

      request_body = {
        contents: [{ parts: [{ text: prompt }] }],
        generationConfig: build_generation_config(options)
      }

      # Add safety settings if provided
      if options[:safety_settings]
        request_body[:safetySettings] = options[:safety_settings].map do |setting|
          {
            category: setting[:category],
            threshold: setting[:threshold]
          }
        end
      end

      apply_moderation(send_request(request_body), options)
    end

    def generate_image_text(image_base64, prompt, options = {})
      raise Error, 'Image is required' if image_base64.nil? || image_base64.empty?

      request_body = {
        contents: [
          { parts: [
            { inline_data: { mime_type: 'image/jpeg', data: image_base64 } },
            { text: prompt }
          ] }
        ],
        generationConfig: build_generation_config(options)
      }

      # Use the pro model for image-to-text tasks
      apply_moderation(send_request(request_body, model: :pro), options)
    end

    def chat(messages, options = {})
      request_body = {
        contents: messages.map { |msg| { role: msg[:role], parts: [{ text: msg[:content] }] } },
        generationConfig: build_generation_config(options)
      }

      # Add system instruction if provided
      if options[:system_instruction]
        request_body[:systemInstruction] = {
          parts: [
            { text: options[:system_instruction] }
          ]
        }
      end

      apply_moderation(send_request(request_body), options)
    end

    private

    def apply_moderation(response, options)
      if options[:moderate]
        moderated, warnings = Utils::Moderation.moderate_text(response)
        warnings.each { |w| self.class.logger.warn(w) } unless warnings.empty?
        moderated
      else
        response
      end
    end

    def resolve_model(model)
      if DEPRECATED_MODELS.key?(model)
        self.class.logger.warn("Model #{model} (#{DEPRECATED_MODELS[model]}) is deprecated and has been removed. " \
                               'Defaulting to :pro (gemini-2.5-pro). Please update your code to use supported models.')
        MODELS[:pro]
      else
        MODELS.fetch(model) do
          self.class.logger.warn("Invalid model: #{model}, defaulting to pro")
          MODELS[:pro]
        end
      end
    end

    def validate_api_key!
      if @api_key.nil? || @api_key.to_s.strip.empty?
        self.class.logger.error('API key is missing')
        raise Error, 'API key is required. Set GEMINI_API_KEY environment variable or pass key directly.'
      end

      # Optional: Add basic API key format validation
      unless valid_api_key_format?(@api_key)
        self.class.logger.error('Invalid API key format')
        raise Error, 'Invalid API key format. Please check your key.'
      end

      # Optional: Check key length and complexity
      return unless @api_key.length < 40

      self.class.logger.warn('Potentially weak API key detected')
    end

    def valid_api_key_format?(key)
      # Strict format check: starts with 'AIza', reasonable length
      key =~ /^AIza[a-zA-Z0-9_-]{35,}$/
    end

    def validate_prompt!(prompt)
      if prompt.nil? || prompt.strip.empty?
        self.class.logger.error('Empty prompt provided')
        raise Error, 'Prompt cannot be empty'
      end

      return unless prompt.length > 8192

      self.class.logger.error('Prompt exceeds maximum length')
      raise Error, 'Prompt too long (max 8192 tokens)'
    end

    def build_generation_config(options)
      {
        temperature: options[:temperature] || 0.7,
        maxOutputTokens: options[:max_tokens] || 1024,
        topP: options[:top_p] || 0.9,
        topK: options[:top_k] || 40
      }
    end

    def send_request(body, model: nil, retry_count: 0)
      # Rate limiting - ensure minimum interval between requests
      rate_limit_delay

      current_model = model ? MODELS.fetch(model) { MODELS[:pro] } : @model
      url = "#{BASE_URL}/#{current_model}:generateContent?key=#{@api_key}"

      # Log URL with masked API key for security
      masked_url = "#{BASE_URL}/#{current_model}:generateContent?key=#{mask_api_key(@api_key)}"
      self.class.logger.debug("Request URL: #{masked_url}")
      self.class.logger.debug("Request Body: #{body.to_json}")

      begin
        response = HTTParty.post(
          url,
          body: body.to_json,
          headers: {
            'Content-Type' => 'application/json',
            'x-goog-api-client' => 'vesper_ruby_gem/0.1.0'
          },
          timeout: 30
        )

        self.class.logger.debug("Response Code: #{response.code}")
        self.class.logger.debug("Response Body: #{response.body}")

        parse_response(response, retry_count, body, model)
      rescue HTTParty::Error, Net::OpenTimeout => e
        self.class.logger.error("API request failed: #{e.message}")
        raise Error, "API request failed: #{e.message}"
      end
    end

    def parse_response(response, retry_count, body, model)
      case response.code
      when 200
        text = response.parsed_response
                       .dig('candidates', 0, 'content', 'parts', 0, 'text')
        text || 'No response generated'
      when 429
        # Rate limit exceeded - implement exponential backoff
        max_retries = 3
        if retry_count < max_retries
          wait_time = (2**retry_count) * 5 # 5, 10, 20 seconds
          self.class.logger.warn("Rate limit hit (429). Retrying in #{wait_time}s (attempt #{retry_count + 1}/#{max_retries})")
          sleep(wait_time)
          send_request(body, model: model, retry_count: retry_count + 1)
        else
          self.class.logger.error("Rate limit exceeded after #{max_retries} retries")
          raise Error, 'Rate limit exceeded. Please check your quota and billing details.'
        end
      else
        error_message = response.parsed_response['error']&.dig('message') || response.body
        self.class.logger.error("API Error: #{error_message}")
        raise Error, "API Error: #{error_message}"
      end
    end

    # Rate limiting to prevent hitting API limits
    def rate_limit_delay
      current_time = Time.now

      if @last_request_time
        time_since_last = current_time - @last_request_time
        if time_since_last < @min_request_interval
          sleep_time = @min_request_interval - time_since_last
          self.class.logger.debug("Rate limiting: sleeping #{sleep_time.round(2)}s")
          sleep(sleep_time)
        end
      end

      @last_request_time = Time.now
    end

    # Mask API key for logging and error reporting
    def mask_api_key(key)
      return '[REDACTED]' if key.nil?

      # Keep first 4 and last 4 characters, replace middle with asterisks
      return key if key.length <= 8

      "#{key[0, 4]}#{'*' * (key.length - 8)}#{key[-4, 4]}"
    end
  end
end
