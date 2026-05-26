# GeminiAI Gem Architecture

## Project Structure

```
vesper/
├── bin/                    # Executable scripts
│   └── gemini             # CLI interface
├── config/                # Configuration files
│   └── environment.rb     # Environment setup
├── docs/                  # Documentation
│   └── ARCHITECTURE.md    # This file
├── examples/              # Usage examples
│   ├── basic_usage.rb     # Basic examples
│   └── advanced.rb  # Configuration examples
├── src/                   # Source code
│   ├── core/              # Core functionality
│   │   ├── client.rb      # Main API client
│   │   ├── errors.rb      # Error classes
│   │   └── version.rb     # Version information
│   ├── utils/             # Utility classes
│   │   ├── loader.rb      # Environment loader
│   │   └── logger.rb      # Logging utility
│   └── vesper.rb       # Main entry point
├── tests/                 # Test suite
│   ├── unit/              # Unit tests
│   │   └── test_client.rb # Client unit tests
│   ├── integration/       # Integration tests
│   │   └── test_api.rb    # API integration tests
│   └── test_runner.rb     # Test runner
├── .env                   # Environment variables (create your own)
├── .gitignore            # Git ignore rules
├── Gemfile               # Dependencies
├── README.md             # Main documentation
└── friday_gemini_ai.gemspec     # Gem specification
```

## Core Components

### 1. Client (`src/core/client.rb`)
- Main API client class
- Handles HTTP requests to Gemini API
- Manages authentication and error handling
- Supports multiple models (Flash, Flash Lite)

### 2. Error Handling (`src/core/errors.rb`)
- Hierarchical error classes
- Specific error types for different scenarios
- Clean error propagation

### 3. Utilities (`src/utils/`)
- **Loader**: Loads environment variables from .env files
- **Logger**: Centralized logging with API key masking

### 4. Configuration (`config/environment.rb`)
- Environment-specific configuration
- Logging level management
- Environment variable validation

## Design Principles

### 1. Separation of Concerns
- Core functionality separated from utilities
- Clear boundaries between components
- Single responsibility principle

### 2. Security First
- API key masking in logs
- Input validation and sanitization
- Secure environment variable handling

### 3. Extensibility
- Modular architecture
- Easy to add new models or features
- Plugin-friendly design

### 4. Developer Experience
- Clear error messages
- Comprehensive examples
- CLI interface for local testing

## Data Flow

```
User Input → Client → API Request → Gemini API → Response → Client → User
     ↓           ↓         ↓            ↓          ↓         ↓       ↓
  Validation → Logging → Security → Network → Parsing → Error → Output
```

## Testing Strategy

### Unit Tests (`tests/unit/`)
- Test individual components in isolation
- Mock external dependencies
- Fast execution

### Integration Tests (`tests/integration/`)
- Test actual API interactions
- Require valid API key
- End-to-end functionality

## Configuration Management

### Environment Variables
- `GEMINI_API_KEY`: Required API key
- `RAILS_ENV`/`RACK_ENV`: Environment detection
- Loaded from `.env` file automatically

### Logging Levels
- **Production**: ERROR only
- **Test**: WARN and above
- **Development**: DEBUG (all messages)

## Error Handling Strategy

### Error Hierarchy
```
StandardError
└── GeminiAI::Error (base)
    ├── APIError
    ├── AuthenticationError
    ├── RateLimitError
    ├── InvalidRequestError
    └── NetworkError
```

### Error Propagation
1. Low-level errors caught and wrapped
2. Meaningful error messages provided
3. API keys masked in error logs
4. Graceful degradation where possible

## Security Considerations

### API Key Protection
- Never logged in plain text
- Masked in all output (logs, errors)
- Validated format before use
- Store secrets in environment variables

### Input Validation
- Prompt length limits
- Content sanitization
- Parameter validation
- Type checking

## Performance Considerations

### HTTP Requests
- Connection timeout (30 seconds)
- Proper error handling for network issues
- Efficient JSON parsing

### Memory Management
- Streaming responses for large content
- Garbage collection friendly
- Minimal object creation

## Extensibility Points

### Adding New Models
1. Update `MODELS` constant in `Client`
2. Add model-specific configuration
3. Update documentation

### Custom Error Types
1. Inherit from `GeminiAI::Error`
2. Add to error hierarchy
3. Update error handling logic

### New Features
1. Add to appropriate module (`core/` or `utils/`)
2. Follow existing patterns
3. Add tests for changed behavior
4. Update documentation
