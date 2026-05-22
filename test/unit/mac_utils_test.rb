# SPDX-License-Identifier: MIT
# Copyright (c) 2026 vesper

require 'test_helper'
require 'mac/mac_utils'

class MacUtilsTest < Minitest::Test
  def test_mac_detection
    skip "Test only runs on macOS" unless GeminiAI::MacUtils.mac?
    assert GeminiAI::MacUtils.mac?
  end

  def test_version_retrieval
    skip "Test only runs on macOS" unless GeminiAI::MacUtils.mac?
    version = GeminiAI::MacUtils.version
    assert version.is_a?(String)
    assert_match(/\d+\.\d+/, version)
  end
end
