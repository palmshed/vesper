# SPDX-License-Identifier: MIT
# Copyright (c) 2026 vesper

#!/usr/bin/env ruby
# frozen_string_literal: true

require 'io/console'
require 'net/http'
require 'json'

class ReleaseHelper
  def self.run
    puts 'Release'

    print 'Continue? (y/N): '
    response = gets.chomp.downcase
    return unless %w[y yes].include?(response)

    puts 'Options:'
    puts '1. Manual'
    puts '2. Secret'

    print 'Choose option (1 or 2): '
    option = gets.chomp

    case option
    when '1'
      manual_release_instructions
    when '2'
      secret_setup_instructions
    else
      puts 'Invalid option. Exiting.'
    end
  end

  def self.manual_release_instructions
    puts 'Manual:'
    puts 'Actions > Release > Run'
  end

  def self.secret_setup_instructions
    print 'OTP: '
    otp = gets.chomp
    puts "Secret: RUBYGEMS_OTP = #{otp}"
  end
end

ReleaseHelper.run if __FILE__ == $PROGRAM_NAME
