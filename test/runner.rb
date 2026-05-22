#!/usr/bin/env ruby
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 vesper
# frozen_string_literal: true

require_relative 'test_helper'

class TestRunner
  TEST_DIRS = [
    'test/unit/**/*_test.rb',
    'test/integration/**/*_test.rb'
  ].freeze

  def self.run
    load_test_files
    run_tests
  end

  def self.load_test_files
    TEST_DIRS.each do |pattern|
      Dir[File.join(__dir__, '..', pattern)].each do |file|
        require file
      end
    end
  end

  def self.run_tests
    puts "\nRunning GeminiAI gem tests..."
    puts "Ruby version: #{RUBY_VERSION}"
    puts "Test directory: #{File.expand_path(File.join(__dir__, '..'))}"
    puts "Test files: #{Minitest::Runnable.runnables.size} test suites loaded"
    puts '-' * 50
  end
end

# Run the tests
TestRunner.run
