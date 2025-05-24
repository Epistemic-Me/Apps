# Evaluation Service Documentation

## Overview
The evaluation service provides conversation evaluation capabilities using the DeepEval framework. It supports both real evaluations using OpenAI's API and mock evaluations for testing and development.

## Key Components

### EvaluationService
- Located in `src/services/evaluation.py`
- Handles both real and mock evaluations
- Uses ConversationalGEval metrics for:
  - User Identification
  - Belief Evidencing
  - Belief Verification

### Test Coverage

#### Core Test Cases (`tests/services/test_evaluation.py`)
1. `test_mock_evaluation`: Verifies basic mock evaluation functionality
2. `test_evaluate_conversation_mock`: Tests conversation evaluation in mock mode
3. `test_evaluate_conversation_real`: Tests conversation evaluation in real mode
4. `test_evaluate_dataset_mock`: Verifies dataset evaluation in mock mode
5. `test_evaluate_dataset_real`: Verifies dataset evaluation in real mode
6. `test_real_openai_evaluation`: Tests integration with OpenAI API
7. `test_missing_api_key`: Verifies error handling for missing API key
8. `test_evaluation_cost_tracking`: Ensures proper cost tracking
9. `test_minimal_test_case`: Tests handling of minimal input
10. `test_metric_evaluation_failure`: Verifies error handling
11. `test_mock_measure_method`: Tests mock measurement functionality
12. `test_real_metric_async_configuration`: Verifies async setup

### Regression Prevention Guide

#### 1. Running Tests
Always run the full test suite before and after making changes:
```bash
cd Apps/sdk-playground
PYTHONPATH=$PYTHONPATH:. pytest tests/services/test_evaluation.py -v
```

#### 2. Key Areas to Test Manually
- Run the Streamlit app in both mock and real modes
- Test the "Run Evaluation" button with various conversations
- Verify metric scores are within expected ranges (0.7-0.95 for mock)
- Check cost tracking accumulation
- Verify async operations complete properly

#### 3. Common Issues and Solutions
- **TypeError: object float can't be used in 'await' expression**
  - Ensure using `a_measure` instead of `measure`
  - Check mock metrics are properly configured for async
- **MissingTestCaseParamsError**
  - Verify context is provided as a list of strings
  - Check all required parameters are included
- **Event loop errors**
  - Use proper async/await patterns
  - Ensure cleanup of async resources

#### 4. Configuration Checklist
- [ ] OpenAI API key properly set in environment
- [ ] Mock mode working without API key
- [ ] Async mode enabled for all metrics
- [ ] Proper error handling for API failures
- [ ] Cost tracking initialized and updating

## Future Improvements

### Short-term
1. Add more granular test cases for specific metrics
2. Implement caching for evaluation results
3. Add retry logic for API failures
4. Improve error messages and user feedback

### Medium-term
1. Add support for custom metrics
2. Implement batch evaluation optimization
3. Add evaluation result persistence
4. Create evaluation result comparison tools

### Long-term
1. Support multiple LLM providers
2. Add automated regression testing
3. Implement evaluation result analytics
4. Create evaluation benchmark suite

## Best Practices

### Code Changes
1. Always update tests when modifying evaluation logic
2. Maintain backward compatibility for mock mode
3. Keep async operations consistent
4. Document new metrics and parameters

### Testing
1. Run full test suite before committing
2. Test both mock and real modes
3. Verify cost tracking accuracy
4. Check error handling paths

### Performance
1. Monitor evaluation latency
2. Track API usage and costs
3. Optimize batch operations
4. Cache results where appropriate

## Troubleshooting

### Common Error Messages
1. "object float can't be used in 'await' expression"
   - Solution: Use `a_measure` instead of `measure`
   - Check async configuration

2. "context must be None or a list of strings"
   - Solution: Provide context as `["string1", "string2"]`
   - Check test case construction

3. "Event loop is closed"
   - Solution: Proper async resource cleanup
   - Check async context management

### Debug Steps
1. Check OpenAI API key configuration
2. Verify metric initialization
3. Monitor async operations
4. Review cost tracking

## API Reference

### EvaluationService
```python
class EvaluationService:
    def __init__(self, use_mock: bool = False):
        """Initialize with mock or real mode"""

    async def evaluate_conversation(self, test_case: ConversationalTestCase) -> dict:
        """Evaluate a single conversation"""

    async def evaluate_dataset(self, dataset: List[ConversationalTestCase]) -> List[dict]:
        """Evaluate multiple conversations"""
```

### Metrics
Each metric provides:
- Async measurement (`a_measure`)
- Score tracking
- Cost tracking
- Error handling

## Dependencies
- deepeval
- openai
- pytest
- pytest-asyncio
- pytest-mock 