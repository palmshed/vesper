# SPDX-License-Identifier: MIT
# Copyright (c) 2026 vesper

# frozen_string_literal: true

require 'logger'

module GeminiAI
  module Utils
    # Centralized logging utility
    class Logger
      def self.instance
        @instance ||= ::Logger.new($stdout).tap do |log|
          log.level = ::Logger::INFO
          log.formatter = proc do |severity, datetime, _progname, msg|
            # Mask any potential API key in logs
            masked_msg = msg.to_s.gsub(/AIza[a-zA-Z0-9_-]{35,}/, '[REDACTED]')
            "#{datetime}: #{severity} -- #{masked_msg}\n"
          end
        end
      end

      def self.debug(message)
        instance.debug(message)
      end

      def self.info(message)
        instance.info(message)
      end

      def self.warn(message)
        instance.warn(message)
      end

      def self.error(message)
        instance.error(message)
      end
    end
  end
end
