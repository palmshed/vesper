# Mac Utils

This module provides macOS-specific utilities for the vesper gem.

## Methods

### `GeminiAI::MacUtils.mac?`

Returns `true` if the current platform is macOS (Darwin), `false` otherwise.

### `GeminiAI::MacUtils.version`

Returns the macOS version string (e.g., "14.1") if running on macOS, `nil` otherwise.

## Usage

```ruby
require 'mac/mac_utils'

if GeminiAI::MacUtils.mac?
  puts "Running on macOS version #{GeminiAI::MacUtils.version}"
end
```
