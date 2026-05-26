# Models

Vesper maps Ruby symbols to Gemini `generateContent` text model IDs.

| Symbol | Model | Use |
| --- | --- | --- |
| `:flash_latest` | `gemini-flash-latest` | Moving Flash alias |
| `:pro_latest` | `gemini-pro-latest` | Moving Pro alias |
| `:flash_3_5` | `gemini-3.5-flash` | Gemini 3.5 Flash |
| `:pro_3_preview` | `gemini-3-pro-preview` | Gemini 3 preview |
| `:flash_3_preview` | `gemini-3-flash-preview` | Gemini 3 Flash preview |
| `:pro_3_1_preview` | `gemini-3.1-pro-preview` | Gemini 3.1 Pro preview |
| `:flash_3_1_lite` | `gemini-3.1-flash-lite` | Gemini 3.1 Flash Lite |
| `:pro_2_5` | `gemini-2.5-pro` | Gemini 2.5 Pro |
| `:flash_2_5` | `gemini-2.5-flash` | Gemini 2.5 Flash |
| `:flash_2_0` | `gemini-2.0-flash` | Gemini 2.0 Flash |
| `:pro` | `gemini-pro-latest` | Short alias |
| `:flash` | `gemini-3.5-flash` | Short alias |
| `:flash_lite` | `gemini-3.1-flash-lite` | Short alias |
| `:pro_2_0` | `gemini-2.0-flash` | Legacy alias |

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
