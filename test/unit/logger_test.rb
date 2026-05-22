# SPDX-License-Identifier: MIT
# Copyright (c) 2026 vesper

# frozen_string_literal: true

require 'test_helper'
require 'stringio'

class LoggerTest < Minitest::Test
  def setup
    @original_stdout = $stdout
    $stdout = StringIO.new
    # Reset the logger instance to ensure clean state
    GeminiAI::Utils::Logger.instance_variable_set(:@instance, nil)
  end

  def teardown
    $stdout = @original_stdout
  end

  def test_logger_initialization
    logger = GeminiAI::Utils::Logger.instance

    assert_instance_of ::Logger, logger
    assert_equal ::Logger::INFO, logger.level
  end

  def test_debug_logging
    logger = GeminiAI::Utils::Logger.instance
    logger.level = ::Logger::DEBUG
    GeminiAI::Utils::Logger.debug('Test debug message')

    assert_includes $stdout.string, 'DEBUG -- Test debug message'
  end

  def test_info_logging
    GeminiAI::Utils::Logger.info('Test info message')

    assert_includes $stdout.string, 'INFO -- Test info message'
  end

  def test_warn_logging
    GeminiAI::Utils::Logger.warn('Test warning message')

    assert_includes $stdout.string, 'WARN -- Test warning message'
  end

  def test_error_logging
    GeminiAI::Utils::Logger.error('Test error message')

    assert_includes $stdout.string, 'ERROR -- Test error message'
  end

  def test_api_key_redaction
    api_key = 'AIzaSyDummyTestKeyForUnitTests123456789'
    GeminiAI::Utils::Logger.info("API key is #{api_key}")

    refute_includes $stdout.string, api_key
    assert_includes $stdout.string, 'INFO -- API key is [REDACTED]'
  end

  def test_log_level_setting
    logger = GeminiAI::Utils::Logger.instance
    logger.level = ::Logger::WARN

    GeminiAI::Utils::Logger.debug('This should not appear')
    GeminiAI::Utils::Logger.warn('This should appear')

    refute_includes $stdout.string, 'DEBUG -- This should not appear'
    assert_includes $stdout.string, 'WARN -- This should appear'
  end

  def test_singleton_instance
    logger1 = GeminiAI::Utils::Logger.instance
    logger2 = GeminiAI::Utils::Logger.instance

    assert_same logger1, logger2
  end
end
