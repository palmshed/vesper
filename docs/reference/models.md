# Models

Vesper maps a small set of Ruby symbols to Gemini model IDs.

| Symbol | Model | Use |
| --- | --- | --- |
| `:pro` | `gemini-2.5-pro` | Default model for complex work |
| `:flash` | `gemini-2.5-flash` | Faster general-purpose responses |
| `:flash_2_0` | `gemini-2.0-flash` | Legacy compatibility |
| `:flash_lite` | `gemini-2.0-flash-lite` | Lightweight legacy compatibility |

## Usage

```ruby
require 'vesper'

client = GeminiAI::Client.new
fast_client = GeminiAI::Client.new(model: :flash)
```

Unknown model symbols fall back to `:pro`.

Deprecated `1.5` aliases log a warning and also fall back to `:pro`.

## Options

Generation options are passed per request:

```ruby
client.generate_text(
  'Explain Ruby fibers',
  temperature: 0.3,
  max_tokens: 500,
  top_p: 0.9,
  top_k: 40
)
```

Use lower temperature for factual output and higher temperature for more varied responses.
