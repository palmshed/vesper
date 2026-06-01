# Versions

<br>

The gem is currently `1.7.0`.

<br>

The published gem name is `friday_gemini_ai`. The runtime entrypoint is `vesper`.

<br>

Gem releases use tags such as `friday_gemini_ai/v1.7.0`. The Vesper Review app is deployed from `main` and is identified by its build commit rather than a gem release tag.

<br>

```ruby
gem 'friday_gemini_ai', require: 'vesper'
```

<br>

# Compatibility

<br>

| Area | Current support |
| --- | --- |
| Ruby | 3.3 or later |
| Local development | Ruby 3.3.11 in `.ruby-version` |
| Gemini API | `v1beta` Generative Language API |
| Default model | `gemini-pro-latest` |
| Fast model | `gemini-3.5-flash` |

<br>

Ruby support follows maintained Ruby branches. The gem currently requires Ruby 3.3 or later; older EOL Rubies are not supported.

<br>

# Public API

<br>

```ruby
require 'vesper'

GeminiAI.load_env
client = GeminiAI::Client.new

client.generate_text('Hello')
client.chat([{ role: 'user', content: 'Hello' }])
```

<br>

Images can be sent as base64 data:

<br>

```ruby
image = Base64.strict_encode64(File.binread('image.jpg'))
client.generate_image_text(image, 'Describe this image')
```

<br>

# Models

<br>

| Symbol | Model |
| --- | --- |
| `:flash_latest` | `gemini-flash-latest` |
| `:pro_latest` | `gemini-pro-latest` |
| `:flash_3_5` | `gemini-3.5-flash` |
| `:pro_3_preview` | `gemini-3-pro-preview` |
| `:flash_3_preview` | `gemini-3-flash-preview` |
| `:pro_3_1_preview` | `gemini-3.1-pro-preview` |
| `:flash_3_1_lite` | `gemini-3.1-flash-lite` |
| `:pro_2_5` | `gemini-2.5-pro` |
| `:flash_2_5` | `gemini-2.5-flash` |
| `:flash_2_0` | `gemini-2.0-flash` |
| `:pro` | `gemini-pro-latest` |
| `:flash` | `gemini-3.5-flash` |
| `:flash_lite` | `gemini-3.1-flash-lite` |
| `:pro_2_0` | `gemini-2.0-flash` |

<br>

Removed aliases resolve to `:pro` with a warning.

<br>

# Updating Versions

<br>

The gem version lives in `lib/core/version.rb`.

<br>

Build locally before publishing:

<br>

```bash
gem build friday_gemini_ai.gemspec
```

<br>

Install the built gem when you need a local package check:

<br>

```bash
gem install friday_gemini_ai-*.gem
```
