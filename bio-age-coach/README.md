# Bio Age Coach

This is an AI-powered coaching application designed to help users understand and optimize their biological age through personalized recommendations based on biomarkers, lifestyle factors, and evidence-based protocols.

## Overview

The Bio Age Coach provides:

1. Analysis of various health metrics related to biological age
2. Personalized recommendations for improving biological age
3. Educational content about biomarkers and longevity
4. Holistic health assessment across multiple data categories
5. Progress tracking and completeness indicators

## Health Data Categories

The application now organizes health data into six key categories, providing a comprehensive assessment of biological age:

1. **Health Data** - Activity metrics from devices like Apple Watch or Fitbit
2. **Bio Age Tests** - Simple functional tests like grip strength or push-up capacity
3. **Capabilities** - Broader functional assessments like VO2 max or reaction time
4. **Biomarkers** - Standard blood and urine test results
5. **Measurements** - Physical measurements like body fat percentage or waist-to-height ratio
6. **Lab Results** - Advanced tests like epigenetic clocks or telomere length

## Features

### Data Completeness Indicators

The application provides visual feedback on the completeness of your health profile:

- Category-specific progress bars
- Overall health profile completeness score
- Radar chart visualization of data coverage
- Personalized suggestions for high-value measurements to add next

### AI Coach Conversation

- Chat interface for interacting with the AI coach
- Biomarker assessment and interpretation
- Protocol recommendations tailored to your data
- Motivation exploration and goal setting
- Plan creation and resource recommendations

## Setup and Installation

### Prerequisites

- Python 3.10+
- pip

### Installation

1. Clone the repository:
```
git clone <repository-url>
cd bio-age-coach
```

2. Create a virtual environment:
```
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```
pip install -r requirements.txt
```

4. Set up your environment variables by creating a `.env` file:
```
OPENAI_API_KEY=your_openai_api_key
CONFIDENT_AI_KEY=your_confident_ai_key
```

### Running the Application

Start the Streamlit app:
```
streamlit run app.py
```

## Development Guide

This section provides detailed instructions for developers working on the Bio Age Coach application, including how to run tests, debug scripts, and evaluations.

### Project Structure

The application is structured as follows:

```
bio-age-coach/
├── app.py                  # Main Streamlit application entry point
├── data/                   # Test and sample data
│   └── test_health_data/   # Test health data for debugging and testing
├── scripts/                # Utility and debug scripts
│   └── debug/              # Debug scripts for testing functionality
├── src/                    # Source code package
│   ├── bio_age_coach/      # Main package
│   │   ├── app.py          # Core application module (not run directly)
│   │   ├── agents/         # Agent implementations
│   │   ├── chatbot/        # Chatbot implementation
│   │   ├── database/       # Database models and utilities
│   │   ├── mcp/            # Multi-Component Protocol implementation
│   │   └── router/         # Query routing implementation
│   └── evaluations/        # Evaluation framework
├── tests/                  # Test suite
│   ├── unit/               # Unit tests
│   ├── integration/        # Integration tests
│   └── conftest.py         # Test fixtures and configuration
└── requirements.txt        # Project dependencies
```

### Running Tests

The project uses pytest for testing. There are several ways to run the tests:

#### Running All Tests

To run all tests:

```bash
cd Apps/bio-age-coach
python -m pytest
```

#### Running Specific Test Categories

To run only unit tests:

```bash
cd Apps/bio-age-coach
python -m pytest tests/unit
```

To run only integration tests:

```bash
cd Apps/bio-age-coach
python -m pytest tests/integration
```

#### Running Individual Test Files

To run a specific test file:

```bash
cd Apps/bio-age-coach
python -m pytest tests/unit/test_router.py
```

#### Running Tests with Verbose Output

For more detailed test output:

```bash
cd Apps/bio-age-coach
python -m pytest -v
```

### Running Debug Scripts

The project includes several debug scripts to test specific functionality without running the full Streamlit application. These scripts are located in the `scripts/debug/` directory and are designed to test different aspects of the application.

#### Preparing Test Data

Before running any debug scripts, ensure you have test data available:

```bash
cd Apps/bio-age-coach
mkdir -p data/test_health_data
# Copy sample data files to the test directory
cp data/*.csv data/test_health_data/
```

#### Available Debug Scripts

The project includes three main debug scripts:

1. **debug_data_upload.py** - Tests the data upload process and observation context creation
2. **debug_observation_contexts.py** - Tests observation context creation and routing
3. **debug_query.py** - Tests query processing and context updates

#### 1. Data Upload Debug Script

This script tests the data upload process and observation context creation:

```bash
cd Apps/bio-age-coach
python scripts/debug/debug_data_upload.py
```

This script will:
1. Initialize MCP servers
2. Load test user data
3. Upload sample health data (sleep, exercise, nutrition, biometric)
4. Check if the observation context is updated
5. Send a query about the uploaded data
6. Verify the response

Example output:
```
=== Starting debug_data_upload test ===
Initializing MCP servers...
Creating MCP client...
Initializing servers...
Uploading sleep data...
Checking if observation context is updated...
Observation context updated successfully!
Sending query about sleep data...
Response: Your average sleep duration is 7.4 hours...
```

#### 2. Observation Contexts Debug Script

This script tests the creation and management of observation contexts:

```bash
cd Apps/bio-age-coach
python scripts/debug/debug_observation_contexts.py
```

This script will:
1. Initialize MCP servers
2. Create various observation contexts (sleep, exercise, nutrition, biometric)
3. Test context relevancy scoring
4. Test context-based routing
5. Verify that the correct agent is selected based on context

Example output:
```
=== Testing Observation Contexts ===
Creating sleep observation context...
Creating exercise observation context...
Testing relevancy scoring...
Sleep context relevancy for sleep query: 0.85
Exercise context relevancy for exercise query: 0.78
Testing context-based routing...
Query routed to HealthDataAgent based on sleep context
```

#### 3. Query Debug Script

This script tests query processing and context updates. It accepts a custom query as a command-line argument:

```bash
cd Apps/bio-age-coach
python scripts/debug/debug_query.py "What does my sleep data tell me about my biological age?"
```

If no query is provided, it will use a default test query.

This script will:
1. Initialize MCP servers
2. Process the provided query
3. Show how the query is routed
4. Display the response
5. Show how the context is updated after the query

Example output:
```
=== Processing Query ===
Query: What does my sleep data tell me about my biological age?
Routing query...
Selected agent: BioAgeScoreAgent (confidence: 0.82)
Response: Based on your sleep data, your biological age indicators suggest...
Updated context: {'active_topic': 'Sleep', 'observation_contexts': {...}}
```

#### Running All Debug Scripts

To run all debug scripts in sequence for comprehensive testing:

```bash
cd Apps/bio-age-coach
for script in scripts/debug/debug_*.py; do
  echo "Running $script..."
  python $script
  echo "------------------------"
done
```

#### Troubleshooting Debug Scripts

If you encounter issues with debug scripts:

1. **Missing Data**: Ensure test data is available in `data/test_health_data/`
2. **API Key**: Verify your OpenAI API key is set in the `.env` file
3. **Import Errors**: Make sure you're running from the project root directory
4. **Path Issues**: If paths are incorrect, try using absolute paths:
   ```bash
   python /full/path/to/Apps/bio-age-coach/scripts/debug/debug_data_upload.py
   ```

### Running Evaluations

The project includes a comprehensive evaluation framework using DeepEval:

#### Running All Evaluations

To run all evaluation suites:

```bash
cd Apps/bio-age-coach
ALL_EVALS=true DEEPEVAL_SAVE_RESULTS=true DEEPEVAL_VERBOSE=true python src/evaluations/bio_age_score_eval.py
```

#### Running Specific Evaluations

To run a specific evaluation suite:

```bash
cd Apps/bio-age-coach
DEEPEVAL_SAVE_RESULTS=true DEEPEVAL_VERBOSE=true python src/evaluations/bio_age_score_eval.py
```

Note: The `DEEPEVAL_SAVE_RESULTS=true` environment variable is required to save results to Confident AI, and `DEEPEVAL_VERBOSE=true` provides detailed output during evaluation.

#### Viewing Results

View detailed evaluation results in Confident AI:

1. Ensure your Confident AI API key is set in the `.env` file:
```
CONFIDENT_AI_KEY=your_confident_ai_key
```

2. Access the dashboard using the URL provided in the evaluation output to view:
   - Test case results
   - Metric scores
   - Performance trends
   - Failure analysis

### Debugging the Application

To debug the Streamlit application:

1. Start the application with debugging enabled:
```bash
cd Apps/bio-age-coach
streamlit run app.py --logger.level=debug
```

2. View logs in the terminal or redirect to a file:
```bash
cd Apps/bio-age-coach
streamlit run app.py --logger.level=debug 2>&1 | tee debug.log
```

## Evaluation Framework

**The** application includes a comprehensive evaluation framework using DeepEval for testing the Bio Age Coach's capabilities across different domains and configurations.

### Test Structure

The evaluation framework is organized into specialized test suites:

- **Biomarker Evaluation** - Tests interpretation of blood tests and other biomarkers
- **Fitness Metrics** - Tests assessment of physical capabilities
- **Health Metrics** - Tests analysis of daily health data
- **Research Integration** - Tests evidence-based recommendations
- **Comprehensive Assessment** - Tests holistic biological age evaluation
- **MCP Server Integration** - Tests Multi-Component Protocol server routing and processing

### Running Tests

#### Basic Test Execution

Run all evaluation suites:
```bash
cd Apps/bio-age-coach
ALL_EVALS=true DEEPEVAL_SAVE_RESULTS=true DEEPEVAL_VERBOSE=true python src/evaluations/bio_age_score_eval.py
```

Run a specific evaluation suite:
```bash
cd Apps/bio-age-coach
DEEPEVAL_SAVE_RESULTS=true DEEPEVAL_VERBOSE=true python src/evaluations/bio_age_score_eval.py
```

Note: The `DEEPEVAL_SAVE_RESULTS=true` environment variable is required to save results to Confident AI, and `DEEPEVAL_VERBOSE=true` provides detailed output during evaluation.

#### Isolated Testing with Router Contexts

The framework supports testing specific server configurations using `RouterContext`:

```python
from evaluations.framework import RouterContext
from bio_age_coach.mcp.health_server import HealthServer
from bio_age_coach.mcp.research_server import ResearchServer

# Test with only health and research servers
context = RouterContext(
    health_server=HealthServer(api_key, data_path="data/test/health"),
    research_server=ResearchServer(api_key, data_path="data/test/research")
)
```

#### MCP Server Configuration Testing

Test different server configurations with custom prompts and tools:

1. Create a test data directory:
```bash
mkdir -p data/test/{health,research,tools}
```

2. Configure server-specific test data:
```python
test_data = {
    "prompts": {
        "system": "Custom system prompt for testing",
        "examples": ["Example 1", "Example 2"]
    },
    "tools": {
        "calculator": {"enabled": True},
        "research": {"enabled": False}
    }
}

# Initialize server with test configuration
await health_server.initialize_data(test_data)
```

### Test Case Creation

Create custom test cases for specific scenarios:

```python
from deepeval.test_case import LLMTestCase

test_case = LLMTestCase(
    input="What does my HbA1c of 5.9% indicate?",
    expected_output="Your HbA1c is in the prediabetic range...",
    retrieval_context=[
        "HbA1c ranges: Normal < 5.7%, Prediabetic 5.7-6.4%",
        "Elevated HbA1c indicates higher average blood sugar"
    ]
)
```

### Evaluation Metrics

The framework uses two primary metrics:

1. **Answer Relevancy** (threshold: 0.7)
   - Measures how well responses address the query
   - Considers context and completeness

2. **Faithfulness** (threshold: 0.7)
   - Measures accuracy and consistency
   - Verifies alignment with provided context

### Viewing Results

View detailed evaluation results in Confident AI:

1. Ensure your Confident AI API key is set in the `.env` file:
```
CONFIDENT_AI_KEY=your_confident_ai_key
```

2. Access the dashboard using the URL provided in the evaluation output to view:
   - Test case results
   - Metric scores
   - Performance trends
   - Failure analysis

### Adding New Test Suites

To create a new evaluation suite:

1. Create a new file in `src/evaluations/`
2. Inherit from `EvaluationSuite`
3. Implement `setup()` and `create_test_cases()`
4. Add the suite to `bio_age_score_eval.py`

Example:
```python
class CustomEvaluation(EvaluationSuite):
    async def setup(self):
        # Initialize test environment
        await super().setup()
    
    def create_test_cases(self) -> List[LLMTestCase]:
        return [
            self.create_test_case(
                input="Custom test query",
                expected_output="Expected response",
                retrieval_context=["Relevant context"]
            )
        ]
```

## Development Roadmap

1. ✅ **Core Chat Interface** - Streamlit-based UI with OpenAI integration
2. ✅ **Biomarker Interpretation** - Assessment of biomarkers and their impact on biological age
3. ✅ **Protocol Recommendations** - Evidence-based suggestions for improving biological age
4. ✅ **Multi-category Health Data** - Support for diverse health metrics across six categories
5. ✅ **Completeness Indicators** - Visual feedback on health profile completeness
6. ⬜ **Advanced Analytics** - Trend analysis and progress tracking over time
7. ⬜ **Mobile Compatibility** - Responsive design for mobile devices
8. ⬜ **Integration with Health Platforms** - Direct import from popular health tracking platforms

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.