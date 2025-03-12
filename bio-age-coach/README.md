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
ALL_EVALS=true python src/evaluations/chatbot_eval.py
```

Run a specific evaluation suite (e.g., fitness metrics):
```bash
cd Apps/bio-age-coach
python src/evaluations/chatbot_eval.py
```

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

1. Login to Confident AI:
```bash
deepeval login --confident-api-key "your-confident-api-key"
```

2. Access the dashboard to view:
   - Test case results
   - Metric scores
   - Performance trends
   - Failure analysis

### Adding New Test Suites

To create a new evaluation suite:

1. Create a new file in `src/evaluations/`
2. Inherit from `EvaluationSuite`
3. Implement `setup()` and `create_test_cases()`
4. Add the suite to `chatbot_eval.py`

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