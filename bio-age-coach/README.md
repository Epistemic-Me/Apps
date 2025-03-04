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

The application includes a comprehensive evaluation framework using DeepEval:

- Test cases covering various aspects of the coach's capabilities
- Metrics for measuring answer relevancy and task completion
- Integration with Confident AI for tracking performance

To run evaluations:
```
python src/evaluations/chatbot_eval.py
```

To view results in Confident AI:
```
deepeval login --confident-api-key "your-confident-api-key"
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