# Cookbook

Practical recipes and code examples for common Vesper use cases.

## Content Generation

### Blog Post Generator
```ruby
class BlogPostGenerator
  def initialize
    @client = GeminiAI::Client.new
  end

  def generate_post(topic, style: 'professional', length: 'medium')
    prompt = build_blog_prompt(topic, style, length)

    @client.generate_text(
      prompt,
      temperature: style == 'creative' ? 0.8 : 0.6,
      max_tokens: length_to_tokens(length)
    )
  end

  private

  def build_blog_prompt(topic, style, length)
    <<~PROMPT
      Write a #{style} blog post about #{topic}.

      Requirements:
      - Length: #{length} (#{length_description(length)})
      - Style: #{style}
      - Include introduction, main points, and conclusion
      - Use engaging headlines and clear structure

      Topic: #{topic}
    PROMPT
  end

  def length_to_tokens(length)
    case length
    when 'short' then 300
    when 'medium' then 600
    when 'long' then 1000
    else 600
    end
  end

  def length_description(length)
    case length
    when 'short' then '2-3 paragraphs'
    when 'medium' then '4-6 paragraphs'
    when 'long' then '7-10 paragraphs'
    else '4-6 paragraphs'
    end
  end
end

# Usage
generator = BlogPostGenerator.new
post = generator.generate_post(
  "Ruby on Rails best practices",
  style: 'technical',
  length: 'medium'
)
puts post
```

### Code Documentation Generator
```ruby
class CodeDocGenerator
  def initialize
    @client = GeminiAI::Client.new
  end

  def document_method(code, language: 'ruby')
    prompt = <<~PROMPT
      Generate comprehensive documentation for this #{language} code:

      ```#{language}
      #{code}
      ```

      Include:
      - Brief description
      - Parameters with types
      - Return value
      - Usage example
      - Any important notes

      Format as markdown.
    PROMPT

    @client.generate_text(prompt, temperature: 0.3, max_tokens: 400)
  end

  def explain_code(code, language: 'ruby')
    prompt = <<~PROMPT
      Explain what this #{language} code does in simple terms:

      ```#{language}
      #{code}
      ```

      Break it down step by step for someone learning to code.
    PROMPT

    @client.generate_text(prompt, temperature: 0.4, max_tokens: 300)
  end
end

# Usage
doc_gen = CodeDocGenerator.new

code = <<~RUBY
  def fibonacci(n)
    return n if n <= 1
    fibonacci(n - 1) + fibonacci(n - 2)
  end
RUBY

documentation = doc_gen.document_method(code)
explanation = doc_gen.explain_code(code)
```

## Chatbot Implementation

### Simple Q&A Bot
```ruby
class QABot
  def initialize(context: nil)
    @client = GeminiAI::Client.new
    @conversation = []
    @context = context

    if @context
      @conversation << {
        role: 'user',
        content: "Context: #{@context}. Please answer questions based on this context."
      }
      @conversation << {
        role: 'model',
        content: "I understand. I'll answer questions based on the provided context."
      }
    end
  end

  def ask(question)
    @conversation << { role: 'user', content: question }

    response = @client.chat(@conversation, temperature: 0.3, max_tokens: 200)

    @conversation << { role: 'model', content: response }

    response
  end

  def reset
    @conversation = []
    if @context
      @conversation << {
        role: 'user',
        content: "Context: #{@context}. Please answer questions based on this context."
      }
      @conversation << {
        role: 'model',
        content: "I understand. I'll answer questions based on the provided context."
      }
    end
  end
end

# Usage
context = "Vesper is a Ruby gem for interacting with Google's Gemini AI models."
bot = QABot.new(context: context)

puts bot.ask("What is Vesper?")
puts bot.ask("How do I install it?")
puts bot.ask("What models does it support?")
```

### Customer Support Bot
```ruby
class SupportBot
  SUPPORT_CONTEXT = <<~CONTEXT
    You are a helpful customer support assistant for Vesper Ruby gem.

    Common issues:
    - API key problems: Check environment variables and key format
    - Rate limiting: Implement exponential backoff
    - Network errors: Check internet connection
    - Installation issues: Ensure Ruby 3.1+ and proper gem installation

    Always be helpful, polite, and provide specific solutions.
  CONTEXT

  def initialize
    @client = GeminiAI::Client.new
    @conversation = [
      { role: 'user', content: SUPPORT_CONTEXT },
      { role: 'model', content: 'I understand. I\'m ready to help with Vesper support questions.' }
    ]
  end

  def handle_query(user_message)
    @conversation << { role: 'user', content: user_message }

    response = @client.chat(
      @conversation,
      temperature: 0.2,  # More consistent responses
      max_tokens: 300
    )

    @conversation << { role: 'model', content: response }

    response
  end
end

# Usage
support = SupportBot.new
puts support.handle_query("I'm getting an 'API key is required' error")
puts support.handle_query("How do I handle rate limiting?")
```

## Data Processing

### Text Summarizer
```ruby
class TextSummarizer
  def initialize
    @client = GeminiAI::Client.new
  end

  def summarize(text, length: 'medium', style: 'bullet_points')
    prompt = build_summary_prompt(text, length, style)

    @client.generate_text(
      prompt,
      temperature: 0.3,
      max_tokens: length_to_tokens(length)
    )
  end

  def extract_key_points(text, count: 5)
    prompt = <<~PROMPT
      Extract the #{count} most important key points from this text:

      #{text}

      Format as a numbered list with brief explanations.
    PROMPT

    @client.generate_text(prompt, temperature: 0.2, max_tokens: 300)
  end

  private

  def build_summary_prompt(text, length, style)
    format_instruction = case style
    when 'bullet_points' then 'Format as bullet points'
    when 'paragraph' then 'Format as a single paragraph'
    when 'structured' then 'Format with clear sections and headings'
    else 'Format as bullet points'
    end

    <<~PROMPT
      Summarize this text in #{length} length:

      #{text}

      #{format_instruction}.
      Focus on the most important information.
    PROMPT
  end

  def length_to_tokens(length)
    case length
    when 'short' then 100
    when 'medium' then 200
    when 'long' then 400
    else 200
    end
  end
end

# Usage
summarizer = TextSummarizer.new

long_article = File.read('article.txt')
summary = summarizer.summarize(long_article, length: 'medium', style: 'bullet_points')
key_points = summarizer.extract_key_points(long_article, count: 3)
```

### Language Translator
```ruby
class LanguageHelper
  def initialize
    @client = GeminiAI::Client.new
  end

  def translate(text, from_lang, to_lang)
    prompt = <<~PROMPT
      Translate this text from #{from_lang} to #{to_lang}:

      #{text}

      Provide only the translation, maintaining the original tone and style.
    PROMPT

    @client.generate_text(prompt, temperature: 0.2, max_tokens: 300)
  end

  def improve_writing(text, style: 'professional')
    prompt = <<~PROMPT
      Improve this text to make it more #{style}:

      #{text}

      Maintain the original meaning while enhancing clarity, grammar, and style.
    PROMPT

    @client.generate_text(prompt, temperature: 0.4, max_tokens: 400)
  end

  def detect_language(text)
    prompt = <<~PROMPT
      What language is this text written in? Respond with just the language name:

      #{text}
    PROMPT

    @client.generate_text(prompt, temperature: 0.1, max_tokens: 50)
  end
end

# Usage
helper = LanguageHelper.new

spanish_text = "Hola, ¿cómo estás?"
english_translation = helper.translate(spanish_text, 'Spanish', 'English')

rough_text = "this is not good writing with bad grammar"
improved_text = helper.improve_writing(rough_text, style: 'professional')
```

## Creative Applications

### Story Generator
```ruby
class StoryGenerator
  def initialize
    @client = GeminiAI::Client.new
  end

  def generate_story(genre:, characters:, setting:, length: 'short')
    prompt = <<~PROMPT
      Write a #{genre} story with the following elements:

      Characters: #{characters.join(', ')}
      Setting: #{setting}
      Length: #{length} story

      Create an engaging narrative with dialogue, conflict, and resolution.
    PROMPT

    @client.generate_text(
      prompt,
      temperature: 0.8,  # High creativity
      max_tokens: story_length_tokens(length)
    )
  end

  def continue_story(existing_story, direction: nil)
    prompt = if direction
      <<~PROMPT
        Continue this story in the direction of: #{direction}

        Existing story:
        #{existing_story}

        Continue the narrative naturally.
      PROMPT
    else
      <<~PROMPT
        Continue this story:

        #{existing_story}

        Continue the narrative naturally with an interesting development.
      PROMPT
    end

    @client.generate_text(prompt, temperature: 0.8, max_tokens: 400)
  end

  private

  def story_length_tokens(length)
    case length
    when 'flash' then 200    # Flash fiction
    when 'short' then 500    # Short story
    when 'medium' then 800   # Longer short story
    else 500
    end
  end
end

# Usage
generator = StoryGenerator.new

story = generator.generate_story(
  genre: 'science fiction',
  characters: ['Dr. Sarah Chen', 'AI Assistant ARIA', 'Captain Rodriguez'],
  setting: 'Space station orbiting Mars in 2157',
  length: 'short'
)

continuation = generator.continue_story(
  story,
  direction: 'mysterious signal from Mars surface'
)
```

### Marketing Copy Generator
```ruby
class MarketingCopyGenerator
  def initialize
    @client = GeminiAI::Client.new
  end

  def generate_ad_copy(product:, audience:, platform:, tone: 'professional')
    prompt = <<~PROMPT
      Create #{platform} ad copy for:

      Product: #{product}
      Target Audience: #{audience}
      Tone: #{tone}
      Platform: #{platform}

      Include:
      - Compelling headline
      - Key benefits
      - Call to action
      - Appropriate hashtags (if social media)

      Keep it concise and engaging for #{platform}.
    PROMPT

    @client.generate_text(
      prompt,
      temperature: 0.7,
      max_tokens: platform_max_tokens(platform)
    )
  end

  def generate_email_subject_lines(topic, count: 5)
    prompt = <<~PROMPT
      Generate #{count} compelling email subject lines for: #{topic}

      Make them:
      - Attention-grabbing
      - Clear and specific
      - Under 50 characters
      - Varied in approach (urgency, curiosity, benefit-focused)

      Format as a numbered list.
    PROMPT

    @client.generate_text(prompt, temperature: 0.8, max_tokens: 200)
  end

  private

  def platform_max_tokens(platform)
    case platform.downcase
    when 'twitter' then 100
    when 'facebook' then 200
    when 'linkedin' then 300
    when 'instagram' then 150
    when 'email' then 400
    else 200
    end
  end
end

# Usage
marketing = MarketingCopyGenerator.new

ad_copy = marketing.generate_ad_copy(
  product: 'Vesper Ruby Gem',
  audience: 'Ruby developers',
  platform: 'LinkedIn',
  tone: 'technical but approachable'
)

subject_lines = marketing.generate_email_subject_lines(
  'New AI features for Ruby developers',
  count: 5
)
```

## Integration Patterns

### Rails Service Integration
```ruby
# app/services/ai_content_service.rb
class AiContentService
  include ActiveModel::Model
  include ActiveModel::Attributes

  attribute :prompt, :string
  attribute :content_type, :string
  attribute :user_id, :integer

  validates :prompt, presence: true, length: { minimum: 10, maximum: 2000 }
  validates :content_type, inclusion: { in: %w[blog_post summary translation] }

  def initialize(attributes = {})
    super
    @client = GeminiAI::Client.new
  end

  def generate
    return false unless valid?

    begin
      response = case content_type
      when 'blog_post'
        generate_blog_post
      when 'summary'
        generate_summary
      when 'translation'
        generate_translation
      else
        @client.generate_text(prompt)
      end

      # Store the result
      AiContent.create!(
        user_id: user_id,
        prompt: prompt,
        response: response,
        content_type: content_type,
        generated_at: Time.current
      )

      response

    rescue GeminiAI::Error => e
      errors.add(:base, "AI generation failed: #{e.message}")
      false
    end
  end

  private

  def generate_blog_post
    @client.generate_text(
      "Write a professional blog post about: #{prompt}",
      temperature: 0.7,
      max_tokens: 800
    )
  end

  def generate_summary
    @client.generate_text(
      "Summarize this content in bullet points: #{prompt}",
      temperature: 0.3,
      max_tokens: 300
    )
  end

  def generate_translation
    # Assuming prompt format: "text|from_lang|to_lang"
    parts = prompt.split('|')
    text, from_lang, to_lang = parts

    @client.generate_text(
      "Translate from #{from_lang} to #{to_lang}: #{text}",
      temperature: 0.2,
      max_tokens: 400
    )
  end
end

# Usage in controller
class AiContentsController < ApplicationController
  def create
    @service = AiContentService.new(ai_content_params.merge(user_id: current_user.id))

    if (response = @service.generate)
      render json: { response: response }, status: :created
    else
      render json: { errors: @service.errors }, status: :unprocessable_entity
    end
  end

  private

  def ai_content_params
    params.require(:ai_content).permit(:prompt, :content_type)
  end
end
```

### Background Job Processing
```ruby
# app/jobs/bulk_content_generation_job.rb
class BulkContentGenerationJob < ApplicationJob
  queue_as :ai_processing

  def perform(batch_id, prompts_data)
    client = GeminiAI::Client.new
    batch = ContentBatch.find(batch_id)

    batch.update!(status: 'processing', started_at: Time.current)

    results = []

    prompts_data.each_with_index do |prompt_data, index|
      begin
        response = client.generate_text(
          prompt_data['prompt'],
          temperature: prompt_data['temperature'] || 0.7,
          max_tokens: prompt_data['max_tokens'] || 300
        )

        results << {
          index: index,
          prompt: prompt_data['prompt'],
          response: response,
          status: 'success'
        }

        # Rate limiting - wait between requests
        sleep(1) unless index == prompts_data.length - 1

      rescue GeminiAI::Error => e
        results << {
          index: index,
          prompt: prompt_data['prompt'],
          error: e.message,
          status: 'failed'
        }
      end

      # Update progress
      progress = ((index + 1).to_f / prompts_data.length * 100).round
      batch.update!(progress: progress)
    end

    # Store results
    batch.update!(
      results: results,
      status: 'completed',
      completed_at: Time.current
    )

    # Notify user
    ContentBatchMailer.completed(batch).deliver_now

  rescue => e
    batch.update!(
      status: 'failed',
      error_message: e.message,
      completed_at: Time.current
    )

    ContentBatchMailer.failed(batch).deliver_now
  end
end

# Usage
prompts = [
  { prompt: "Write about Ruby", temperature: 0.7 },
  { prompt: "Explain AI", temperature: 0.3 },
  { prompt: "Create a story", temperature: 0.9 }
]

batch = ContentBatch.create!(
  user: current_user,
  total_prompts: prompts.length,
  status: 'queued'
)

BulkContentGenerationJob.perform_later(batch.id, prompts)
```

## Testing Patterns

### RSpec Testing
```ruby
# spec/services/ai_content_service_spec.rb
RSpec.describe AiContentService do
  let(:service) { described_class.new(prompt: "Test prompt", content_type: "blog_post", user_id: 1) }

  describe '#generate' do
    context 'when API call succeeds' do
      before do
        allow_any_instance_of(GeminiAI::Client).to receive(:generate_text)
          .and_return('Generated content')
      end

      it 'creates an AiContent record' do
        expect { service.generate }.to change(AiContent, :count).by(1)
      end

      it 'returns the generated content' do
        result = service.generate
        expect(result).to eq('Generated content')
      end
    end

    context 'when API call fails' do
      before do
        allow_any_instance_of(GeminiAI::Client).to receive(:generate_text)
          .and_raise(GeminiAI::APIError.new('API Error'))
      end

      it 'adds error to service' do
        service.generate
        expect(service.errors[:base]).to include('AI generation failed: API Error')
      end

      it 'returns false' do
        expect(service.generate).to be_falsey
      end
    end
  end
end

# spec/support/vesper_helpers.rb
module GeminiAIHelpers
  def stub_gemini_success(response = 'Test response')
    allow_any_instance_of(GeminiAI::Client).to receive(:generate_text)
      .and_return(response)
  end

  def stub_gemini_failure(error_class = GeminiAI::APIError, message = 'Test error')
    allow_any_instance_of(GeminiAI::Client).to receive(:generate_text)
      .and_raise(error_class.new(message))
  end
end

RSpec.configure do |config|
  config.include GeminiAIHelpers
end
```

This cookbook provides practical, ready-to-use code examples for common scenarios. Each recipe includes complete working code that developers can adapt for their specific needs.
