import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import random  # for mock evaluations
from dotenv import load_dotenv
from deepeval import evaluate
from deepeval.metrics import (
    AnswerRelevancyMetric,
    FaithfulnessMetric,
    HallucinationMetric,
    ConversationalGEval
)
from deepeval.test_case.conversational_test_case import ConversationalTestCase
from deepeval.test_case.llm_test_case import LLMTestCaseParams

from ..models.base import DialogueInteraction, EvaluationResult

# Load environment variables from .env file
load_dotenv()

class EvaluationService:
    def __init__(self, use_mock: bool = False):
        """Initialize the evaluation service with ConversationalGEval metrics
        
        Args:
            use_mock: If True, use mock evaluations instead of real ones
        """
        self.use_mock = use_mock
        self.evaluation_cost = 0.0
        
        if not self.use_mock:
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY in your .env file.")
            
            # Initialize metrics based on CONVERSATIONAL_EVAL.md specifications
            self.metrics = {
                "User Identification": ConversationalGEval(
                    name="User Identification",
                    evaluation_steps=[
                        "1. Check if the user's cohort membership is clear and consistent",
                        "2. Identify specific characteristics that place them in their cohort",
                        "3. Look for unique identifiers in responses that confirm cohort alignment",
                        "4. Assess confidence in user's demographic and psychographic profile"
                    ],
                    evaluation_params=[
                        LLMTestCaseParams.INPUT,
                        LLMTestCaseParams.ACTUAL_OUTPUT,
                        LLMTestCaseParams.CONTEXT
                    ],
                    model='gpt-4o',
                    threshold=0.7,
                    async_mode=True,
                    verbose_mode=False
                ),
                "Belief Evidencing": ConversationalGEval(
                    name="Belief Evidencing",
                    evaluation_steps=[
                        "1. Check if user shares personal experiences supporting their beliefs",
                        "2. Assess if experiences are specific and detailed enough to be credible",
                        "3. Verify clear connection between experiences and stated beliefs",
                        "4. Evaluate consistency of evidencing patterns across different beliefs"
                    ],
                    evaluation_params=[
                        LLMTestCaseParams.INPUT,
                        LLMTestCaseParams.ACTUAL_OUTPUT,
                        LLMTestCaseParams.CONTEXT
                    ],
                    model='gpt-4o',
                    threshold=0.7,
                    async_mode=True,
                    verbose_mode=False
                ),
                "Belief Verification": ConversationalGEval(
                    name="Belief Verification",
                    evaluation_steps=[
                        "1. Check if output aligns with user's existing belief system",
                        "2. Verify new concepts are introduced building on existing beliefs",
                        "3. Identify potential cognitive dissonance and how it's addressed",
                        "4. Assess evidence suggesting user will find output credible"
                    ],
                    evaluation_params=[
                        LLMTestCaseParams.INPUT,
                        LLMTestCaseParams.ACTUAL_OUTPUT,
                        LLMTestCaseParams.CONTEXT
                    ],
                    model='gpt-4o',
                    threshold=0.7,
                    async_mode=True,
                    verbose_mode=False
                )
            }
        else:
            # Create mock metrics that behave like real ones but return random scores
            self.metrics = {}
            for metric_name in ["User Identification", "Belief Evidencing", "Belief Verification"]:
                mock_metric = ConversationalGEval(
                    name=metric_name,
                    evaluation_steps=["1. Mock evaluation"],
                    evaluation_params=[
                        LLMTestCaseParams.INPUT,
                        LLMTestCaseParams.ACTUAL_OUTPUT,
                        LLMTestCaseParams.CONTEXT  # Add context parameter
                    ],
                    model='gpt-4o',
                    threshold=0.7,
                    async_mode=True,
                    verbose_mode=False
                )
                # Override the a_measure method to return random scores
                mock_metric.a_measure = self._create_mock_measure(mock_metric)
                mock_metric.score = 0.0
                mock_metric.evaluation_cost = 0.1
                self.metrics[metric_name] = mock_metric

    def _create_mock_measure(self, metric):
        """Create a mock measure method that returns random scores"""
        async def mock_measure(test_case, _show_indicator=True):
            score = self._mock_evaluate()
            # Set the score on the metric instance
            metric.score = score
            metric.evaluation_cost = 0.1
            self.evaluation_cost += metric.evaluation_cost
            return score
        return mock_measure

    def _mock_evaluate(self) -> float:
        """Generate a mock evaluation score between 0.7 and 0.95"""
        return random.uniform(0.7, 0.95)

    async def evaluate_conversation(self, test_case: ConversationalTestCase) -> dict:
        """
        Evaluate a single conversation using the configured metrics.
        Returns a dictionary mapping metric names to their scores.
        """
        results = {}
        for metric_name, metric in self.metrics.items():
            # Use a_measure for both mock and real modes
            await metric.a_measure(test_case)
            results[metric_name] = metric.score
            if not self.use_mock:  # Only track cost for real evaluations
                self.evaluation_cost += metric.evaluation_cost
        
        return results

    async def evaluate_dataset(self, dataset: List[ConversationalTestCase]) -> List[Dict[str, float]]:
        """
        Evaluate a dataset of conversations using the configured metrics.
        Returns a list of dictionaries mapping metric names to their scores.
        """
        results = []
        for test_case in dataset:
            conversation_results = await self.evaluate_conversation(test_case)
            results.append(conversation_results)
        return results 