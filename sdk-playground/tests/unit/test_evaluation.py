import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock
from src.services.evaluation import EvaluationService
from deepeval.test_case import LLMTestCase, ConversationalTestCase

@pytest.fixture
def sample_test_case():
    """Create a sample test case for evaluation"""
    return ConversationalTestCase(
        turns=[
            LLMTestCase(
                input="How can I improve my biological age?",
                actual_output="Regular exercise can improve your biological age.",
                expected_output=None,
                context=["user_cohort: health_conscious", "router_intent: Lower BioAge Score"]
            ),
            LLMTestCase(
                input="I understand, and I agree that exercise is important.",
                actual_output="That's great! Would you like specific exercise recommendations?",
                expected_output=None,
                context=["user_cohort: health_conscious", "router_intent: Lower BioAge Score"]
            )
        ]
    )

@pytest.fixture
def evaluator():
    """Create an evaluator instance in mock mode"""
    return EvaluationService(use_mock=True)

@pytest.mark.asyncio
async def test_evaluate_conversation(evaluator, sample_test_case):
    """Test evaluating a single conversation"""
    result = await evaluator.evaluate_conversation(sample_test_case)
    assert result is not None
    assert isinstance(result, dict)
    assert all(0.7 <= score <= 0.95 for score in result.values())

@pytest.mark.asyncio
async def test_evaluate_dataset(evaluator):
    """Test evaluating multiple conversations"""
    # Create a small dataset of test cases
    dataset = [
        ConversationalTestCase(
            turns=[
                LLMTestCase(
                    input=f"Test input {i}",
                    actual_output=f"Test output {i}",
                    expected_output=None,
                    context=["user_cohort: health_conscious", "router_intent: Lower BioAge Score"]
                )
            ]
        )
        for i in range(3)
    ]
    results = await evaluator.evaluate_dataset(dataset)
    assert results is not None
    assert len(results) == len(dataset)
    assert all(isinstance(result, dict) for result in results)

@pytest.mark.asyncio
async def test_mock_evaluation(evaluator):
    """Test that mock evaluations return expected ranges"""
    # Create a simple test case
    test_case = ConversationalTestCase(
        turns=[
            LLMTestCase(
                input="test input",
                actual_output="test output",
                expected_output=None,
                context=["user_cohort: test_cohort", "router_intent: Lower BioAge Score"]
            )
        ]
    )
    result = await evaluator.evaluate_conversation(test_case)
    assert result is not None
    assert isinstance(result, dict)
    assert all(0.7 <= score <= 0.95 for score in result.values())

@pytest.mark.asyncio
async def test_evaluate_interaction(evaluator, sample_test_case):
    """Test that individual metrics are called correctly"""
    # Mock the metric measure methods
    async def mock_measure_user_id(test_case):
        evaluator.metrics["User Identification"].score = 0.8
        return 0.8
    async def mock_measure_belief_ev(test_case):
        evaluator.metrics["Belief Evidencing"].score = 0.85
        return 0.85
    async def mock_measure_belief_ver(test_case):
        evaluator.metrics["Belief Verification"].score = 0.9
        return 0.9

    evaluator.metrics["User Identification"].a_measure = AsyncMock(side_effect=mock_measure_user_id)
    evaluator.metrics["Belief Evidencing"].a_measure = AsyncMock(side_effect=mock_measure_belief_ev)
    evaluator.metrics["Belief Verification"].a_measure = AsyncMock(side_effect=mock_measure_belief_ver)

    result = await evaluator.evaluate_conversation(sample_test_case)
    
    # Verify metrics were called with correct test case
    evaluator.metrics["User Identification"].a_measure.assert_called_once_with(sample_test_case)
    evaluator.metrics["Belief Evidencing"].a_measure.assert_called_once_with(sample_test_case)
    evaluator.metrics["Belief Verification"].a_measure.assert_called_once_with(sample_test_case)
    
    # Verify results format
    assert result is not None
    assert isinstance(result, dict)
    assert result["User Identification"] == 0.8
    assert result["Belief Evidencing"] == 0.85
    assert result["Belief Verification"] == 0.9

@pytest.mark.asyncio
async def test_batch_evaluate(evaluator):
    """Test evaluating multiple conversations in batch"""
    # Create multiple test cases
    test_cases = [
        ConversationalTestCase(
            turns=[
                LLMTestCase(
                    input=f"Message {i}",
                    actual_output=f"Response {i}",
                    expected_output=None,
                    context=["user_cohort: health_conscious", "router_intent: Lower BioAge Score"]
                )
            ]
        )
        for i in range(3)
    ]
    
    # Mock the metric measure methods
    async def mock_measure_user_id(test_case):
        evaluator.metrics["User Identification"].score = 0.8
        return 0.8
    async def mock_measure_belief_ev(test_case):
        evaluator.metrics["Belief Evidencing"].score = 0.85
        return 0.85
    async def mock_measure_belief_ver(test_case):
        evaluator.metrics["Belief Verification"].score = 0.9
        return 0.9

    evaluator.metrics["User Identification"].a_measure = AsyncMock(side_effect=mock_measure_user_id)
    evaluator.metrics["Belief Evidencing"].a_measure = AsyncMock(side_effect=mock_measure_belief_ev)
    evaluator.metrics["Belief Verification"].a_measure = AsyncMock(side_effect=mock_measure_belief_ver)
    
    results = await evaluator.evaluate_dataset(test_cases)
    
    # Verify metrics were called for each test case
    assert evaluator.metrics["User Identification"].a_measure.call_count == len(test_cases)
    assert evaluator.metrics["Belief Evidencing"].a_measure.call_count == len(test_cases)
    assert evaluator.metrics["Belief Verification"].a_measure.call_count == len(test_cases)
    
    # Verify results format
    assert results is not None
    assert len(results) == len(test_cases)
    assert all(isinstance(result, dict) for result in results)
    assert all(result["User Identification"] == 0.8 for result in results)
    assert all(result["Belief Evidencing"] == 0.85 for result in results)
    assert all(result["Belief Verification"] == 0.9 for result in results)

@pytest.mark.asyncio
async def test_evaluation_metrics_range(evaluator, sample_test_case):
    """Test that metrics return scores within expected ranges"""
    result = await evaluator.evaluate_conversation(sample_test_case)
    
    # Verify all scores are within expected range
    assert result is not None
    assert isinstance(result, dict)
    assert all(0.7 <= score <= 0.95 for score in result.values()) 