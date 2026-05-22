# frozen_string_literal: true
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 vesper

require 'test_helper'
require 'tempfile'
require 'fileutils'

class TestLoader < Minitest::Test
  def setup
    @temp_dir = Dir.mktmpdir('vesper_test')
    @env_file = File.join(@temp_dir, '.env')
  end

  def teardown
    FileUtils.remove_entry(@temp_dir) if File.directory?(@temp_dir)
    # Clean up any environment variables we might have set
    ENV.delete('TEST_KEY')
    ENV.delete('ANOTHER_KEY')
  end

  def test_load_with_valid_env_file
    # Create a test .env file
    File.open(@env_file, 'w') do |f|
      f.puts 'TEST_KEY=test_value'
      f.puts 'ANOTHER_KEY=another_value'
      f.puts '# This is a comment'
      f.puts '   ' # Empty line with whitespace
    end

    # Load the environment variables
    GeminiAI::Utils::Loader.load(@env_file)

    # Check that the environment variables were set correctly
    assert_equal 'test_value', ENV.fetch('TEST_KEY', nil)
    assert_equal 'another_value', ENV.fetch('ANOTHER_KEY', nil)
  end

  def test_load_with_nonexistent_file
    # This should not raise an error
    refute_path_exists('nonexistent_file')
    GeminiAI::Utils::Loader.load('nonexistent_file')
  end

  def test_load_with_empty_file
    # Create an empty .env file
    FileUtils.touch(@env_file)

    # This should not raise an error
    GeminiAI::Utils::Loader.load(@env_file)
  end

  def test_load_with_malformed_line
    # Create a .env file with a malformed line
    File.open(@env_file, 'w') do |f|
      f.puts 'MALFORMED_LINE'
      f.puts 'GOOD_KEY=good_value'
      f.puts 'ANOTHER_KEY=another_value'
    end

    # This should not raise an error
    GeminiAI::Utils::Loader.load(@env_file)

    # The well-formed lines should still be processed
    assert_equal 'good_value', ENV.fetch('GOOD_KEY', nil)
    assert_equal 'another_value', ENV.fetch('ANOTHER_KEY', nil)
    assert_nil ENV.fetch('MALFORMED_LINE', nil)
  end

  def test_load_with_complex_values
    # Test with values containing special characters and complex values
    File.open(@env_file, 'w') do |f|
      f.puts 'URL=https://example.com?param=value&another=param'
      f.puts 'JSON_DATA={"key": "value", "nested": {"a": 1}}'
      f.puts 'SPECIAL_CHARS=!@#$%^&*()_+{}|:"<>?[];\',.`~'
      f.puts 'WITH_EQUALS=key=value'
      f.puts 'WITH_HASH=value#not_a_comment'
    end

    GeminiAI::Utils::Loader.load(@env_file)

    # Check that the environment variables were set correctly
    assert_equal 'https://example.com?param=value&another=param', ENV.fetch('URL', nil)
    assert_equal '{"key": "value", "nested": {"a": 1}}', ENV.fetch('JSON_DATA', nil)
    assert_equal '!@#$%^&*()_+{}|:"<>?[];\',.`~', ENV.fetch('SPECIAL_CHARS', nil)
    assert_equal 'key=value', ENV.fetch('WITH_EQUALS', nil)
    assert_equal 'value#not_a_comment', ENV.fetch('WITH_HASH', nil)
  end
end
