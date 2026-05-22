# frozen_string_literal: true

namespace :docs do
  desc 'Generate YARD documentation'
  task :generate do
    sh 'yard doc --output-dir doc "lib/**/*.rb" README.md'
  end

  desc 'Start a local documentation server'
  task :preview do
    puts 'Starting YARD documentation server at http://localhost:8808'
    puts 'Press CTRL+C to stop'
    system('yard server -r -p 8808')
  end
end

desc 'Alias for docs:generate'
task docs: 'docs:generate'
