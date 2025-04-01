# Conversational Evaluation Implementation Plan

## Overview
This document outlines the implementation plan for using DeepEval's Conversational GEval to evaluate dialectic interactions between Coach and User, focusing on biological age coaching conversations with context-aware evaluation.

## Custom Metrics

### 1. User Identification Metric
```python
user_identification_metric = ConversationalGEval(
    name="User Identification",
    criteria="""Evaluate how well we understand the user's identity and context within their cohort.
    Consider:
    1. Is the user's cohort membership clear and consistent?
    2. Do we identify specific characteristics that place them in their cohort?
    3. Are there unique identifiers in their responses that confirm cohort alignment?
    4. How confident are we in the user's demographic and psychographic profile?""",
    evaluation_params=[
        LLMTestCaseParams.INPUT,
        LLMTestCaseParams.ACTUAL_OUTPUT,
        LLMTestCaseParams.CONTEXT
    ]
)
```

### 2. Belief Evidencing Metric
```python
belief_evidencing_metric = ConversationalGEval(
    name="Belief Evidencing",
    criteria="""Analyze how well the user provides experiential evidence for their beliefs.
    Consider:
    1. Does the user share personal experiences that support their beliefs?
    2. Are the experiences specific and detailed enough to be credible?
    3. Is there a clear connection between experiences and stated beliefs?
    4. How consistent are the evidencing patterns across different beliefs?""",
    evaluation_params=[
        LLMTestCaseParams.INPUT,
        LLMTestCaseParams.ACTUAL_OUTPUT,
        LLMTestCaseParams.CONTEXT
    ]
)
```

### 3. Belief Verification Metric
```python
belief_verification_metric = ConversationalGEval(
    name="Belief Verification",
    criteria="""Assess the likelihood that the user will accept and internalize the prompt output.
    Consider:
    1. Does the output align with the user's existing belief system?
    2. Are new concepts introduced in a way that builds on existing beliefs?
    3. Is there potential cognitive dissonance, and how is it addressed?
    4. What evidence suggests the user will find the output credible?""",
    evaluation_params=[
        LLMTestCaseParams.INPUT,
        LLMTestCaseParams.ACTUAL_OUTPUT,
        LLMTestCaseParams.CONTEXT
    ]
)
```

### 4. Ambiguity Assessment Metric
```python
ambiguity_metric = ConversationalGEval(
    name="Ambiguity Assessment",
    criteria="""Measure the level of ambiguity the user might perceive in the interaction.
    Consider:
    1. Are concepts explained at an appropriate level for the user's background?
    2. Are there potential multiple interpretations of key points?
    3. How well are technical terms defined and contextualized?
    4. Are there unaddressed assumptions that might create confusion?""",
    evaluation_params=[
        LLMTestCaseParams.INPUT,
        LLMTestCaseParams.ACTUAL_OUTPUT,
        LLMTestCaseParams.CONTEXT
    ]
)
```

### 5. Learning Progress Metric
```python
learning_progress_metric = ConversationalGEval(
    name="Learning Progress",
    criteria="""Evaluate how much we've learned about the user during the session.
    Consider:
    1. What new information about the user has been revealed?
    2. How has our understanding of their belief system evolved?
    3. What gaps in our knowledge about the user have been filled?
    4. How has the depth of user understanding increased over time?""",
    evaluation_params=[
        LLMTestCaseParams.INPUT,
        LLMTestCaseParams.ACTUAL_OUTPUT,
        LLMTestCaseParams.CONTEXT
    ]
)
```

### 6. Answer Prediction Metric
```python
answer_prediction_metric = ConversationalGEval(
    name="Answer Prediction",
    criteria="""Assess our ability to predict the user's responses based on accumulated knowledge.
    Consider:
    1. How well can we anticipate the user's answers to new questions?
    2. What patterns in their responses have we identified?
    3. How consistent are their answers with our predictions?
    4. What factors improve or decrease our prediction accuracy?""",
    evaluation_params=[
        LLMTestCaseParams.INPUT,
        LLMTestCaseParams.ACTUAL_OUTPUT,
        LLMTestCaseParams.CONTEXT
    ]
)
```

### 7. Question Clarity Metric
```python
question_clarity_metric = ConversationalGEval(
    name="Question Clarity",
    criteria="""Evaluate our ability to identify the most informative next question.
    Consider:
    1. How well do we target knowledge gaps about the user?
    2. Is the question appropriate for the current context and user state?
    3. Does the question build on previous responses effectively?
    4. How likely is the question to yield useful new information?""",
    evaluation_params=[
        LLMTestCaseParams.INPUT,
        LLMTestCaseParams.ACTUAL_OUTPUT,
        LLMTestCaseParams.CONTEXT
    ]
)
```

## Context-Aware Evaluation System

### Context Structure
```python
@dataclass
class EvaluationContext:
    user_cohort: str
    belief_system: Dict[str, float]
    demographic_data: Dict[str, Any]
    session_history: List[Dict]
    learning_objectives: List[str]
    confidence_scores: Dict[str, float]
    
    def to_dict(self) -> Dict:
        """Convert context to dictionary for DeepEval"""
        return asdict(self)
```

### Test Case Format with Context
```python
from deepeval.test_case import ConversationalTestCase, LLMTestCase

test_case = ConversationalTestCase(
    turns=[
        LLMTestCase(
            input="What factors influence biological age?",
            actual_output="Biological age is influenced by various lifestyle factors...",
            context=EvaluationContext(
                user_cohort="health_conscious_professional",
                belief_system={
                    "health_important": 0.8,
                    "exercise_beneficial": 0.7,
                    "aging_controllable": 0.6
                },
                demographic_data={
                    "age_range": "35-45",
                    "education_level": "graduate",
                    "lifestyle": "active"
                },
                session_history=[],
                learning_objectives=[
                    "understand_biological_age",
                    "identify_lifestyle_factors"
                ],
                confidence_scores={
                    "user_identification": 0.85,
                    "belief_understanding": 0.75
                }
            ).to_dict()
        ),
        # Additional turns...
    ]
)
```

## UI Components for Context Configuration

### Context Configuration Component
```python
# src/ui/components/context_config.py
class ContextConfigurationPanel:
    def __init__(self):
        self.context = EvaluationContext()
        
    def render_cohort_selector(self):
        """Render cohort selection dropdown"""
        pass
        
    def render_belief_system_editor(self):
        """Render belief system configuration interface"""
        pass
        
    def render_demographic_editor(self):
        """Render demographic data input form"""
        pass
        
    def render_objectives_config(self):
        """Render learning objectives configuration"""
        pass
        
    def get_context(self) -> Dict:
        """Return current context configuration"""
        return self.context.to_dict()
```

### Evaluation Dashboard Integration
```python
# src/ui/components/evaluation_dashboard.py
class EvaluationDashboard:
    def __init__(self):
        self.context_config = ContextConfigurationPanel()
        self.metric_suite = MetricSuite()
        
    def configure_context(self):
        """Configure evaluation context through UI"""
        st.sidebar.title("Evaluation Context")
        context = self.context_config.render()
        return context
        
    async def evaluate_conversation(self, conversation: List[Dict], context: Dict):
        """Evaluate conversation with configured context"""
        test_case = self.create_test_case(conversation, context)
        results = await self.metric_suite.evaluate_conversation(test_case)
        self.display_results(results)
```

## Implementation Steps

1. Context System Implementation
   ```python
   # src/evaluation/context.py
   class ContextManager:
       def validate_context(self, context: Dict) -> bool:
           """Validate context data"""
           pass
           
       def enrich_context(self, context: Dict) -> Dict:
           """Enrich context with derived data"""
           pass
   ```

2. Metric Implementation with Context
   ```python
   # src/evaluation/metrics.py
   class ContextAwareMetricSuite:
       def __init__(self):
           self.metrics = [
               user_identification_metric,
               belief_evidencing_metric,
               belief_verification_metric,
               ambiguity_metric,
               learning_progress_metric,
               answer_prediction_metric,
               question_clarity_metric
           ]
           self.context_manager = ContextManager()
           
       async def evaluate_with_context(self, test_case: ConversationalTestCase, context: Dict):
           """Evaluate conversation with context"""
           enriched_context = self.context_manager.enrich_context(context)
           test_case.update_context(enriched_context)
           return await self.evaluate_conversation(test_case)
   ```

## Testing Strategy

### Context-Aware Unit Tests
```python
# tests/unit/test_context_aware_metrics.py
async def test_context_validation():
    """Test context validation logic"""
    pass

async def test_context_enrichment():
    """Test context enrichment process"""
    pass

async def test_metrics_with_context():
    """Test metrics using different contexts"""
    pass
```

### Integration Tests
```python
# tests/integration/test_context_evaluation.py
async def test_full_context_aware_evaluation():
    """Test complete evaluation pipeline with context"""
    pass

async def test_ui_context_configuration():
    """Test UI context configuration flow"""
    pass
```

## Next Steps
1. Implement context management system
2. Create UI components for context configuration
3. Implement context-aware metrics
4. Develop context validation and enrichment
5. Create test suite for context-aware evaluation
6. Integrate with existing dashboard

Would you like me to:
1. Start implementing the context management system?
2. Begin with the UI components for context configuration?
3. Create the test suite for context-aware metrics?
4. Implement any specific metric first? 