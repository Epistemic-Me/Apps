# SDK Playground

## Overview
A development and testing environment for the Bio Age Coach SDK, featuring evaluation services, dataset generation, and UI components for testing and visualization.

## Documentation

### Core Documentation
- [Evaluation Service](docs/evaluation_service.md) - Comprehensive guide to the evaluation service
- [Test Plan](docs/test_plan.md) - Detailed test coverage and future plans
- [Dataset Generation](docs/dataset_generation.md) - Guide to generating and testing datasets

### Key Features
1. Evaluation Service
   - Real and mock evaluation modes
   - OpenAI API integration
   - Cost tracking
   - Async operation support

2. Dataset Generation
   - Sample conversation generation
   - Context generation
   - Test case conversion
   - Multiple dataset support

3. UI Components
   - Conversation visualization
   - Metrics display
   - Dataset selection
   - Real-time evaluation

## Setup

### Prerequisites
- Python 3.8+
- OpenAI API key (for real evaluations)
- Streamlit

### Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Install test dependencies
pip install -r requirements-test.txt
```

### Environment Setup
```bash
# Copy example environment file
cp .env.example .env

# Add your OpenAI API key
echo "OPENAI_API_KEY=your-key-here" >> .env
```

## Running Tests

### Unit Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/services/test_evaluation.py
```

### UI Tests
```bash
# Run UI component tests
pytest tests/ui/

# Run with verbose output
pytest -v tests/ui/
```

## Common Issues

### OpenAI API
1. Rate Limiting
   - Implement exponential backoff
   - Use mock mode for testing
   - Monitor usage

2. Cost Management
   - Track evaluation costs
   - Set usage limits
   - Use mock mode for development

### UI
1. Loading States
   - Check component mounting
   - Verify async operations
   - Test error handling

2. State Management
   - Monitor memory usage
   - Clear state appropriately
   - Handle race conditions

## Contributing
1. Create feature branch
2. Add tests for new features
3. Update documentation
4. Submit pull request

## License
[License details here] 