"""
Evaluation framework for the Bio Age Coach system.
"""

from typing import Dict, Any, List, Optional
from deepeval.test_case import ConversationalTestCase, LLMTestCase, LLMTestCaseParams
from deepeval.metrics import ConversationalGEval
from deepeval import evaluate
import os
import asyncio
import json
from datetime import datetime, timedelta
import random
from bio_age_coach.agents.specialized.bio_age_score_agent import BioAgeScoreAgent
from bio_age_coach.mcp.client import MultiServerMCPClient
from bio_age_coach.router.semantic_router import SemanticRouter
from bio_age_coach.router.router_adapter import RouterAdapter

class RouterContext:
    """Context for router-based evaluations."""
    
    def __init__(self, mcp_client: MultiServerMCPClient):
        """Initialize the router context."""
        self.mcp_client = mcp_client
        self.user_id = "test_user"
        self.context = {}

class EvaluationSuite:
    """Base class for evaluation suites."""
    
    def __init__(self, context: RouterContext):
        """Initialize the evaluation suite."""
        self.context = context
        self.mcp_client = context.mcp_client
        
        # Initialize agent for testing
        api_key = os.getenv("OPENAI_API_KEY", "test_key")
        self.bio_age_score_agent = BioAgeScoreAgent(
            name="BioAgeScoreAgent",
            description="I analyze health metrics to calculate and explain biological age scores.",
            api_key=api_key,
            mcp_client=self.mcp_client
        )
        
        # Initialize router with agent
        self.semantic_router = SemanticRouter(
            api_key=api_key,
            agents=[self.bio_age_score_agent]
        )
        
        # Initialize router adapter
        self.router = RouterAdapter(
            semantic_router=self.semantic_router,
            mcp_client=self.mcp_client
        )
        
        # Define metrics with enhanced configuration
        self.metrics = [
            ConversationalGEval(
                name="Response Accuracy",
                criteria=(
                    "Determine if the actual output accurately addresses the input query and matches the expected output. "
                    "Consider the following aspects:\n"
                    "1. Does the response directly answer the question?\n"
                    "2. Are all relevant metrics mentioned with correct values and units?\n"
                    "3. Is the response structured similarly to the expected output?\n"
                    "4. Are the recommendations specific and actionable?\n"
                    "5. Does it maintain consistent formatting throughout?"
                ),
                evaluation_params=[
                    LLMTestCaseParams.INPUT,
                    LLMTestCaseParams.ACTUAL_OUTPUT,
                    LLMTestCaseParams.EXPECTED_OUTPUT,
                    LLMTestCaseParams.CONTEXT
                ],
                strict_mode=True,
                threshold=0.7
            ),
            
            ConversationalGEval(
                name="Scientific Accuracy",
                criteria=(
                    "Evaluate if the actual output contains scientifically accurate information. "
                    "Consider the following aspects:\n"
                    "1. Are all scientific claims supported by evidence?\n"
                    "2. Are health recommendations aligned with established guidelines?\n"
                    "3. Is the interpretation of metrics medically sound?\n"
                    "4. Are limitations and uncertainties appropriately acknowledged?\n"
                    "5. Is the information presented in a balanced way without exaggeration?"
                ),
                evaluation_params=[
                    LLMTestCaseParams.ACTUAL_OUTPUT,
                    LLMTestCaseParams.CONTEXT
                ],
                strict_mode=True,
                threshold=0.7
            )
        ]
    
    async def setup(self) -> None:
        """Set up the test environment."""
        pass
    
    def create_test_cases(self) -> List[ConversationalTestCase]:
        """Create test cases for evaluation."""
        return []
    
    async def run_evaluation(self) -> List[ConversationalTestCase]:
        """Run the evaluation and return test cases with results."""
        # Set up the test environment
        await self.setup()
        
        # Create test cases
        test_cases = self.create_test_cases()
        
        # Run evaluation
        results = evaluate(test_cases, metrics=self.metrics)
        
        return test_cases 