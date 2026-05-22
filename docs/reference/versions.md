# Versions

Vesper is currently `1.7.0`.

The published gem name is `friday_gemini_ai`. The runtime entrypoint is `vesper`.

```ruby
gem 'friday_gemini_ai', require: 'vesper'
```

## Compatibility

| Area | Current support |
| --- | --- |
| Ruby | 3.1 or later |
| Local development | Ruby 3.2.2 in `.ruby-version` |
| Gemini API | `v1` Generative Language API |
| Default model | `gemini-2.5-pro` |
| Fast model | `gemini-2.5-flash` |

## Public API

```ruby
require 'vesper'

GeminiAI.load_env
client = GeminiAI::Client.new

client.generate_text('Hello')
client.chat([{ role: 'user', content: 'Hello' }])
```

Images can be sent as base64 data:

```ruby
image = Base64.strict_encode64(File.binread('image.jpg'))
client.generate_image_text(image, 'Describe this image')
```

## Models

| Symbol | Model |
| --- | --- |
| `:pro` | `gemini-2.5-pro` |
| `:flash` | `gemini-2.5-flash` |
| `:flash_2_0` | `gemini-2.0-flash` |
| `:flash_lite` | `gemini-2.0-flash-lite` |

Older `1.5` model aliases are deprecated and resolve to `:pro`.

## Updating Versions

The gem version lives in `lib/core/version.rb`.

Build locally before publishing:

```bash
gem build friday_gemini_ai.gemspec
```

Install the built gem when you need a local package check:

```bash
gem install friday_gemini_ai-*.gem
```
