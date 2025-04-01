# Dataset Generation and Testing

## Overview
The dataset generation system provides tools for creating realistic conversation datasets for testing and development. It uses the `DatasetGenerator` class to create sample conversations with realistic context, turns, and metrics.

## Components

### DatasetGenerator
Located in `src/data/dataset_generator.py`

#### Key Features
- Sample belief system generation
- Conversation turn generation
- Context generation with:
  - User cohort information
  - Belief systems
  - Demographic data
  - Session history
  - Learning objectives
  - Confidence scores

#### Methods
```python
class DatasetGenerator:
    def generate_sample_context(self) -> Dict:
        """Generate a sample evaluation context"""

    def generate_sample_conversation(self, dataset_index: int = 0) -> Conversation:
        """Generate a sample conversation with turns and metrics"""

    def generate_test_case(self, conversation: Conversation) -> ConversationalTestCase:
        """Convert a conversation to a DeepEval test case"""

    def generate_evaluation_dataset(self, num_conversations: int = 5) -> EvaluationDataset:
        """Generate a dataset with multiple conversations"""

    def generate_multiple_datasets(self, dataset_configs: List[Dict]) -> List[EvaluationDataset]:
        """Generate multiple named datasets"""
```

### Generated Data Structure

#### Context
```python
{
    "user_cohort": str,
    "router_intent": str,  # AI Coach Router Intent (e.g., "Lower BioAge Score")
    "belief_system": Dict[str, float],
    "demographic_data": Dict[str, str],
    "session_history": List[Dict],
    "learning_objectives": List[str],
    "confidence_scores": Dict[str, float]
}
```

#### Router Intents
The system supports the following AI Coach Router Intents:
- Lower BioAge Score: Focus on strategies to improve biological age
- Query Health Analysis: Analyze current health status and metrics
- Research Health: Explore health topics and gather information
- View Health Data as Visualization: Present health data in visual formats

#### Conversation
- Turns with coach and user messages
- Belief updates tracking
- Timestamps
- Metrics for evaluation

## Usage

### Basic Dataset Generation
```python
from src.data.dataset_generator import DatasetGenerator

# Initialize generator
generator = DatasetGenerator()

# Generate a single dataset
dataset = generator.generate_evaluation_dataset(num_conversations=5)

# Generate multiple datasets
datasets = generator.generate_multiple_datasets([
    {"name": "Health Conscious Professionals", "num_conversations": 3},
    {"name": "Fitness Enthusiasts", "num_conversations": 3}
])
```

### Testing with Generated Datasets
```python
# In your test file
from src.data.dataset_generator import DatasetGenerator

def test_evaluation_with_generated_data():
    generator = DatasetGenerator()
    dataset = generator.generate_evaluation_dataset(num_conversations=1)
    
    # Use dataset for testing
    evaluation_service = EvaluationService()
    results = await evaluation_service.evaluate_dataset(dataset)
    
    # Verify results
    assert len(results) == 1
    assert all(0.7 <= score <= 0.95 for score in results[0].values())
```

## Testing Strategy

### Unit Tests
1. Test individual generator methods
2. Verify context structure
3. Check conversation generation
4. Validate metrics ranges

### Integration Tests
1. Test dataset generation with evaluation service
2. Verify UI rendering of generated data
3. Test persistence and loading

### Data Quality Tests
1. Verify belief system consistency
2. Check context completeness
3. Validate metric ranges
4. Test conversation coherence

## Best Practices

### Dataset Generation
1. Use realistic conversation templates
2. Maintain belief system consistency
3. Generate diverse scenarios
4. Include edge cases

### Testing
1. Use fixed random seeds for reproducibility
2. Test with various dataset sizes
3. Verify all required fields
4. Check data consistency

## Future Improvements

### Short-term
1. Add more conversation templates
2. Improve belief system dynamics
3. Add validation for generated data
4. Enhance metric generation

### Medium-term
1. Add more user cohorts
2. Implement conversation branching
3. Add more context types
4. Improve data variety

### Long-term
1. ML-based data generation
2. Real conversation integration
3. Advanced scenario generation
4. Automated data validation

## Troubleshooting

### Common Issues
1. Inconsistent belief updates
   - Check belief system tracking
   - Verify update logic

2. Invalid context format
   - Verify context structure
   - Check string formatting

3. Metric range violations
   - Check metric calculations
   - Verify range constraints

### Debug Steps
1. Print generated context
2. Verify conversation structure
3. Check metric calculations
4. Validate belief updates

## Dependencies
- uuid
- dataclasses
- datetime
- deepeval 