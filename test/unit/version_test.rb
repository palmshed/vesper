# SPDX-License-Identifier: MIT
# Copyright (c) 2026 vesper

# frozen_string_literal: true

require 'test_helper'

class VersionTest < Minitest::Test
  def test_version
    refute_nil GeminiAI::VERSION
    assert_match(/\d+\.\d+\.\d+/, GeminiAI::VERSION)
  end
end
