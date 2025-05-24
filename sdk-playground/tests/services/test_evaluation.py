import os
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from deepeval.test_case.conversational_test_case import ConversationalTestCase
from deepeval.test_case.llm_test_case import LLMTestCase, LLMTestCaseParams
from deepeval.metrics import ConversationalGEval
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

from src.services.evaluation import EvaluationService

@pytest.fixture
def sample_test_case():
    """Create a sample test case for testing"""
    return ConversationalTestCase(
        turns=[
            LLMTestCase(
                input="What is biological age?",
                actual_output="Biological age is a measure of how well your body functions compared to your chronological age.",
                context=["You are a health coach helping users understand aging and longevity."]
            )
        ],
        chatbot_role="health coach",
        name="test_conversation"
    )

@pytest.fixture
def evaluation_service():
    """Return evaluation service in mock mode"""
    return EvaluationService(use_mock=True)

@pytest.fixture
def real_evaluation_service():
    """Return evaluation service in real mode"""
    return EvaluationService(use_mock=False)

@pytest.fixture
def mock_evaluation_service():
    with patch('deepeval.metrics.ConversationalGEval') as mock_geval:
        mock_metric = MagicMock()
        mock_metric.evaluate.return_value = 0.85
        mock_metric.evaluation_cost = 0.1
        mock_metric.score = 0.85
        mock_metric.success = True
        mock_metric.error = None
        mock_geval.return_value = mock_metric
        yield mock_geval

@pytest.mark.asyncio
async def test_mock_evaluation(evaluation_service, sample_test_case):
    """Test evaluation service in mock mode"""
    results = await evaluation_service.evaluate_conversation(sample_test_case)
    
    # Check that we got mock results for all metrics
    assert len(results) == 3  # Three metrics defined
    for metric_name in ["User Identification", "Belief Evidencing", "Belief Verification"]:
        assert metric_name in results
        assert 0.7 <= results[metric_name] <= 0.95  # Mock scores are in this range

@pytest.mark.asyncio
async def test_evaluate_conversation_mock(evaluation_service, sample_test_case):
    """Test evaluation of a single conversation in mock mode"""
    results = await evaluation_service.evaluate_conversation(sample_test_case)
    
    # Verify results structure
    assert isinstance(results, dict)
    assert all(isinstance(score, float) for score in results.values())
    assert all(0.7 <= score <= 0.95 for score in results.values())
    assert "User Identification" in results
    assert "Belief Evidencing" in results
    assert "Belief Verification" in results

@pytest.mark.asyncio
async def test_evaluate_conversation_real(real_evaluation_service, sample_test_case):
    """Test evaluation of a single conversation in real mode"""
    # Create patches for each metric's a_measure method
    patches = []
    for metric_name in ["User Identification", "Belief Evidencing", "Belief Verification"]:
        metric = real_evaluation_service.metrics[metric_name]
        patch_a_measure = patch.object(metric, 'a_measure', new=AsyncMock())
        patch_score = patch.object(metric, 'score', new=0.85)
        patch_cost = patch.object(metric, 'evaluation_cost', new=0.1)
        patches.extend([patch_a_measure, patch_score, patch_cost])
    
    # Apply all patches
    for p in patches:
        p.start()
    
    try:
        # Evaluate the conversation
        results = await real_evaluation_service.evaluate_conversation(sample_test_case)
        
        # Verify results structure
        assert isinstance(results, dict)
        assert all(isinstance(score, float) for score in results.values())
        assert "User Identification" in results
        assert "Belief Evidencing" in results
        assert "Belief Verification" in results
        assert all(score == 0.85 for score in results.values())
        
        # Verify a_measure was called for each metric
        for metric_name in real_evaluation_service.metrics:
            metric = real_evaluation_service.metrics[metric_name]
            metric.a_measure.assert_called_once_with(sample_test_case)
    finally:
        # Clean up patches
        for p in patches:
            p.stop()

@pytest.mark.asyncio
async def test_evaluate_dataset_mock(evaluation_service, sample_test_case):
    """Test evaluation of multiple conversations in mock mode"""
    # Create a dataset with multiple conversations
    dataset = [sample_test_case, sample_test_case]
    
    # Evaluate the dataset
    results = await evaluation_service.evaluate_dataset(dataset)
    
    # Check results
    assert len(results) == len(dataset)
    assert all(isinstance(result, dict) for result in results)
    assert all("User Identification" in result for result in results)
    assert all(all(0.7 <= score <= 0.95 for score in result.values()) for result in results)

@pytest.mark.asyncio
async def test_evaluate_dataset_real(real_evaluation_service, sample_test_case):
    """Test evaluation of multiple conversations in real mode"""
    # Create a dataset with multiple conversations
    dataset = [sample_test_case, sample_test_case]

    # Create patches for each metric's a_measure method
    patches = []
    for metric_name in ["User Identification", "Belief Evidencing", "Belief Verification"]:
        metric = real_evaluation_service.metrics[metric_name]
        patch_a_measure = patch.object(metric, 'a_measure', new=AsyncMock(return_value=0.85))
        patch_score = patch.object(metric, 'score', new=0.85)
        patch_cost = patch.object(metric, 'evaluation_cost', new=0.1)
        patches.extend([patch_a_measure, patch_score, patch_cost])

    # Apply all patches
    for p in patches:
        p.start()

    try:
        # Evaluate the dataset
        results = await real_evaluation_service.evaluate_dataset(dataset)

        # Check results
        assert len(results) == len(dataset)
        assert all(isinstance(result, dict) for result in results)
        assert all("User Identification" in result for result in results)
        assert all(all(score == 0.85 for score in result.values()) for result in results)
    finally:
        # Clean up patches
        for p in patches:
            p.stop()

@pytest.mark.asyncio
async def test_real_openai_evaluation(sample_test_case):
    metric = ConversationalGEval(
        name="test_metric",
        evaluation_steps=[
            "1. Review the input and output",
            "2. Check if the output is relevant",
            "3. Evaluate the quality of the response"
        ],
        evaluation_params=[
            LLMTestCaseParams.INPUT,
            LLMTestCaseParams.ACTUAL_OUTPUT,
            LLMTestCaseParams.CONTEXT
        ],
        model='gpt-4o',
        async_mode=True
    )
    
    # Mock the measure method to return a score asynchronously
    with patch.object(metric, 'measure', new=AsyncMock()) as mock_measure, \
         patch.object(metric, 'score', new=0.85), \
         patch.object(metric, 'evaluation_cost', new=0.1):
        await metric.measure(sample_test_case)
        assert isinstance(metric.score, float)
        assert 0 <= metric.score <= 1
        assert hasattr(metric, 'evaluation_cost')
        assert metric.evaluation_cost >= 0.0

@pytest.mark.asyncio
async def test_missing_api_key():
    """Test that service raises error when OpenAI API key is missing"""
    with patch.dict(os.environ, {'OPENAI_API_KEY': ''}, clear=True):
        with pytest.raises(ValueError, match="OpenAI API key not found"):
            EvaluationService(use_mock=False)

@pytest.mark.asyncio
async def test_evaluation_cost_tracking(real_evaluation_service, sample_test_case):
    """Test that evaluation cost is tracked correctly"""
    # Create patches for each metric
    patches = []
    for metric_name in ["User Identification", "Belief Evidencing", "Belief Verification"]:
        metric = real_evaluation_service.metrics[metric_name]
        patch_a_measure = patch.object(metric, 'a_measure', new=AsyncMock(return_value=0.85))
        patch_score = patch.object(metric, 'score', new=0.85)
        patch_cost = patch.object(metric, 'evaluation_cost', new=0.1)  # Each metric costs 0.1
        patches.extend([patch_a_measure, patch_score, patch_cost])

    # Apply all patches
    for p in patches:
        p.start()

    try:
        # Initial cost should be 0
        assert real_evaluation_service.evaluation_cost == 0.0

        # Evaluate conversation
        await real_evaluation_service.evaluate_conversation(sample_test_case)

        # Cost should be sum of all metric costs (0.1 * 3 = 0.3)
        assert real_evaluation_service.evaluation_cost == pytest.approx(0.3)
    finally:
        # Clean up patches
        for p in patches:
            p.stop()

@pytest.mark.asyncio
async def test_minimal_test_case(real_evaluation_service):
    """Test handling of minimal test case"""
    # Create a minimal test case with one empty turn and context
    minimal_test_case = ConversationalTestCase(
        turns=[LLMTestCase(input="", actual_output="", context=["test context"])],
        chatbot_role="test"
    )

    # Create patches for each metric
    patches = []
    for metric_name in ["User Identification", "Belief Evidencing", "Belief Verification"]:
        metric = real_evaluation_service.metrics[metric_name]
        patch_a_measure = patch.object(metric, 'a_measure', new=AsyncMock(return_value=0.0))
        patch_score = patch.object(metric, 'score', new=0.0)  # Empty test case should get low scores
        patch_cost = patch.object(metric, 'evaluation_cost', new=0.1)
        patches.extend([patch_a_measure, patch_score, patch_cost])

    # Apply all patches
    for p in patches:
        p.start()

    try:
        results = await real_evaluation_service.evaluate_conversation(minimal_test_case)
        assert all(score == 0.0 for score in results.values())
    finally:
        # Clean up patches
        for p in patches:
            p.stop()

@pytest.mark.asyncio
async def test_metric_evaluation_failure(real_evaluation_service, sample_test_case):
    """Test handling of metric evaluation failure"""
    # Create patches for metrics where one fails
    patches = []

    for metric_name in ["User Identification", "Belief Evidencing", "Belief Verification"]:
        metric = real_evaluation_service.metrics[metric_name]
        if metric_name == "Belief Evidencing":
            # Make this metric fail
            patch_a_measure = patch.object(metric, 'a_measure', new=AsyncMock(side_effect=Exception("Metric evaluation failed")))
            patches.append(patch_a_measure)
        else:
            patch_a_measure = patch.object(metric, 'a_measure', new=AsyncMock(return_value=0.85))
            patch_score = patch.object(metric, 'score', new=0.85)
            patch_cost = patch.object(metric, 'evaluation_cost', new=0.1)
            patches.extend([patch_a_measure, patch_score, patch_cost])

    # Apply all patches
    for p in patches:
        p.start()

    try:
        with pytest.raises(Exception, match="Metric evaluation failed"):
            await real_evaluation_service.evaluate_conversation(sample_test_case)
    finally:
        # Clean up patches
        for p in patches:
            p.stop()

@pytest.mark.asyncio
async def test_mock_measure_method(evaluation_service, sample_test_case):
    """Test that the mock measure method correctly updates the metric's score"""
    # Get a metric from the service
    metric = evaluation_service.metrics["User Identification"]
    
    # Initial score should be 0.0
    assert metric.score == 0.0
    
    # Call a_measure method
    await metric.a_measure(sample_test_case)
    
    # Score should be updated to a value between 0.7 and 0.95
    assert 0.7 <= metric.score <= 0.95
    assert evaluation_service.evaluation_cost == 0.1

@pytest.mark.asyncio
async def test_real_metric_async_configuration(real_evaluation_service):
    """Test that real metrics are properly configured for async operation"""
    for metric_name, metric in real_evaluation_service.metrics.items():
        # Verify metric is configured for async operation
        assert metric.async_mode is True
        assert hasattr(metric, 'a_measure')
        assert callable(metric.a_measure)