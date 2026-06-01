# Mac Utils

<br>

This module provides macOS-specific utilities for the vesper gem.

<br>

# Methods

<br>

# `GeminiAI::MacUtils.mac?`

<br>

Returns `true` if the current platform is macOS (Darwin), `false` otherwise.

<br>

# `GeminiAI::MacUtils.version`

<br>

Returns the macOS version string (e.g., "14.1") if running on macOS, `nil` otherwise.

<br>

# Usage

<br>

```ruby
require 'mac/mac_utils'

if GeminiAI::MacUtils.mac?
  puts "Running on macOS version #{GeminiAI::MacUtils.version}"
end
```
