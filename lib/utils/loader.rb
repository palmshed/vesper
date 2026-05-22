# SPDX-License-Identifier: MIT
# Copyright (c) 2026 vesper

# frozen_string_literal: true

module GeminiAI
  module Utils
    # Utility class for loading environment variables from .env files
    class Loader
      def self.load(file_path = '.env')
        return unless File.exist?(file_path)

        File.readlines(file_path).each do |line|
          line = line.strip
          next if line.empty? || line.start_with?('#')

          key, value = line.split('=', 2)
          ENV[key] = value if key && value
        end
      end
    end
  end
end
