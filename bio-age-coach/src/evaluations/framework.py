"""
Evaluation framework for Bio Age Coach.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Type
import asyncio
import time
import os
from difflib import SequenceMatcher
from deepeval.test_case import ConversationalTestCase, LLMTestCase, LLMTestCaseParams
from deepeval.metrics import (
    ConversationalGEval,
    HallucinationMetric,
    BiasMetric,
    BaseMetric,
    ConversationRelevancyMetric,
    KnowledgeRetentionMetric,
    ConversationCompletenessMetric,
    RoleAdherenceMetric
)
from bio_age_coach.mcp.servers.health_server import HealthServer
from bio_age_coach.mcp.servers.research_server import ResearchServer
from bio_age_coach.mcp.servers.tools_server import ToolsServer
from bio_age_coach.mcp.utils.client import MultiServerMCPClient
from bio_age_coach.mcp.core.router import QueryRouter
from bio_age_coach.mcp.core.module_registry import ModuleRegistry
from bio_age_coach.mcp.modules.bio_age_score_module import BioAgeScoreModule
from bio_age_coach.types import DataCategory
from bio_age_coach.mcp.servers.bio_age_score_server import BioAgeScoreServer

class ExactMatchMetric(BaseMetric):
    """Metric that checks for exact match between actual and expected output."""
    
    def __init__(self, threshold: float = 0.5):
        """Initialize the metric with a threshold."""
        self.threshold = threshold
    
    def measure(self, test_case: ConversationalTestCase) -> float:
        """Measure exact match score."""
        if test_case.actual_output == test_case.expected_output:
            return 1.0
        return 0.0

class SimilarityMetric(BaseMetric):
    """Metric that measures string similarity between actual and expected output."""
    
    def __init__(self, threshold: float = 0.5):
        """Initialize the metric with a threshold."""
        self.threshold = threshold
    
    def measure(self, test_case: ConversationalTestCase) -> float:
        """Measure similarity score using SequenceMatcher."""
        return SequenceMatcher(None, test_case.actual_output, test_case.expected_output).ratio()

class KeywordMatchMetric(BaseMetric):
    """Metric that checks for presence of key phrases from expected output."""
    
    def __init__(self, threshold: float = 0.5):
        """Initialize the metric with a threshold."""
        self.threshold = threshold
    
    def measure(self, test_case: ConversationalTestCase) -> float:
        """Measure keyword match score."""
        if not test_case.actual_output or not test_case.expected_output:
            return 0.0
            
        # Extract key phrases from expected output
        expected_phrases = [p.strip() for p in test_case.expected_output.lower().split(',')]
        actual_lower = test_case.actual_output.lower()
        
        # Count matches
        matches = sum(1 for phrase in expected_phrases if phrase in actual_lower)
        return matches / len(expected_phrases) if expected_phrases else 0.0

class ContextRelevanceMetric(BaseMetric):
    """Metric that checks if the response uses information from the context."""
    
    def __init__(self, threshold: float = 0.5):
        """Initialize the metric with a threshold."""
        self.threshold = threshold
    
    def measure(self, test_case: ConversationalTestCase) -> float:
        """Measure context relevance score."""
        if not test_case.actual_output or not test_case.retrieval_context:
            return 0.0
            
        # Check how many context items are referenced in the response
        actual_lower = test_case.actual_output.lower()
        context_matches = sum(1 for ctx in test_case.retrieval_context 
                            if any(phrase.lower() in actual_lower 
                                  for phrase in ctx.split()))
        
        return context_matches / len(test_case.retrieval_context)

@dataclass
class RouterContext:
    """Context for routing queries to specific MCP servers."""
    mcp_client: Optional[MultiServerMCPClient] = None
    
    def get_active_servers(self) -> List[str]:
        """Get list of active servers in this context."""
        if not self.mcp_client:
            return []
        return list(self.mcp_client.servers.keys())

class ContextualQueryRouter(QueryRouter):
    """Query router that respects context boundaries."""
    
    def __init__(self, context: RouterContext):
        super().__init__(module_registry=context.module_registry)
        self.context = context
    
    async def route_query(self, query: str) -> Dict[str, Any]:
        """Route query respecting context boundaries."""
        active_servers = self.context.get_active_servers()
        # Only route to servers that are active in this context
        response = await super().route_query(query)
        if response.get("server") not in active_servers:
            return {"error": f"Server {response.get('server')} not available in current context"}
        return response

class EvaluationSuite:
    """Base class for evaluation suites."""
    
    def __init__(self, context: RouterContext):
        """Initialize the evaluation suite."""
        self.context = context
        self.mcp_client = context.mcp_client
        
        # Initialize module registry
        self.module_registry = ModuleRegistry()
        self.module_registry.register_module("bio_age_score", BioAgeScoreModule)
        
        # Initialize router with mcp_client and module_registry
        self.router = QueryRouter(mcp_client=self.mcp_client, module_registry=self.module_registry)
        
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
                name="Medical Accuracy",
                criteria=(
                    "Determine if the medical information and recommendations are accurate and evidence-based. "
                    "Consider the following aspects:\n"
                    "1. Are health metrics interpreted correctly with reference ranges?\n"
                    "2. Are recommendations supported by clinical guidelines?\n"
                    "3. Is advice appropriate for user demographics?\n"
                    "4. Is safety considered in recommendations?\n"
                    "5. Are medical terms used accurately?"
                ),
                evaluation_params=[
                    LLMTestCaseParams.ACTUAL_OUTPUT,
                    LLMTestCaseParams.CONTEXT,
                    LLMTestCaseParams.RETRIEVAL_CONTEXT
                ],
                strict_mode=True,
                threshold=0.7
            ),
            ConversationRelevancyMetric(
                window_size=3,  # Consider last 3 turns for relevancy
                threshold=0.7
            ),
            KnowledgeRetentionMetric(
                threshold=0.7
            ),
            ConversationCompletenessMetric(
                threshold=0.7
            ),
            RoleAdherenceMetric(
                threshold=0.7
            ),
            HallucinationMetric(threshold=0.7),
            BiasMetric(threshold=0.7)
        ]
        
        # Rate limiting settings
        self.last_api_call = 0
        self.min_delay_between_calls = 1  # seconds between API calls
        self.max_retries = 3
        self.retry_delay = 60  # seconds
    
    async def setup(self):
        """Setup the evaluation environment."""
        try:
            # Generate test data
            test_data = {
                "user_id": "test_user_123",
                "health_data": [],  # Will be populated by module
                "habits": {},       # Will be populated by module
                "plan": {}         # Will be populated by module
            }
            
            # Initialize module if not already initialized
            if not hasattr(self, 'module'):
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    raise ValueError("OPENAI_API_KEY environment variable is not set")
                self.module = BioAgeScoreModule(api_key, self.context.mcp_client)
            
            # Initialize module with test data
            await self.module.initialize(test_data)
            
        except Exception as e:
            print(f"Setup error: {e}")
            raise
    
    async def teardown(self):
        """Cleanup test environment."""
        pass
    
    def create_test_cases(self) -> List[ConversationalTestCase]:
        """Create test cases for this evaluation suite."""
        raise NotImplementedError
    
    def create_test_case(self, input: str, expected_output: str, context: List[str], retrieval_context: List[str]) -> ConversationalTestCase:
        """Helper method to create a test case with actual_output initialized to None."""
        llm_test_case = LLMTestCase(
            input=input,
            actual_output=None,  # Initialize as None, will be set during evaluation
            expected_output=expected_output,
            context=context,
            retrieval_context=retrieval_context
        )
        return ConversationalTestCase(
            turns=[llm_test_case],
            chatbot_role="Bio Age Coach"
        )
    
    async def _wait_for_rate_limit(self):
        """Wait for rate limit to reset."""
        current_time = time.time()
        time_since_last_call = current_time - self.last_api_call
        if time_since_last_call < self.min_delay_between_calls:
            delay = self.min_delay_between_calls - time_since_last_call
            print(f"\nWaiting {delay:.1f} seconds for rate limit...")
            await asyncio.sleep(delay)
        self.last_api_call = time.time()
    
    async def _process_test_case(self, test_case: ConversationalTestCase) -> Optional[ConversationalTestCase]:
        """Process a single test case with retries for rate limits."""
        retries = 0
        while retries < self.max_retries:
            try:
                await self._wait_for_rate_limit()
                
                # Get the last turn's input
                last_turn = test_case.turns[-1]
                
                # Route the query through the module
                response = await self.module._process_request({
                    "action": "query",
                    "message": last_turn.input,
                    "user_id": "test_user"
                })
                
                # Extract response content
                if isinstance(response, dict):
                    # Build response from various components
                    response_parts = []
                    
                    # Add prompt if available
                    if "prompt" in response:
                        response_parts.append(response["prompt"])
                    
                    # Add scores if available
                    if "scores" in response:
                        scores = response["scores"]
                        if isinstance(scores, list) and scores:
                            latest_score = scores[-1]
                            response_parts.append(f"Current Score: {latest_score.get('total_score', 0)}/120 points")
                            response_parts.append(f"- Sleep Component: {latest_score.get('sleep_score', 0)}/60")
                            response_parts.append(f"- Exercise Component: {latest_score.get('exercise_score', 0)}/30")
                            response_parts.append(f"- Movement Component: {latest_score.get('steps_score', 0)}/30")
                    
                    # Add trends if available
                    if "trends" in response:
                        trends = response["trends"]
                        if isinstance(trends, dict):
                            response_parts.append("\nTrends:")
                            for component, trend in trends.items():
                                response_parts.append(f"- {component}: {trend}")
                    
                    # Add recommendations if available
                    if "recommendations" in response:
                        recommendations = response["recommendations"]
                        if isinstance(recommendations, list):
                            response_parts.append("\nRecommendations:")
                            for rec in recommendations:
                                response_parts.append(f"- {rec}")
                    
                    # Add any other response content
                    if "response" in response:
                        response_parts.append(response["response"])
                    
                    # Combine all parts
                    actual_output = "\n".join(response_parts)
                else:
                    actual_output = str(response)
                
                # Update the actual output
                last_turn.actual_output = actual_output
                print(f"✓ Processed test case: {last_turn.input[:50]}...")
                return test_case
                
            except Exception as e:
                print(f"Error processing test case (attempt {retries + 1}): {e}")
                retries += 1
                if retries < self.max_retries:
                    print(f"Retrying in {self.retry_delay} seconds...")
                    await asyncio.sleep(self.retry_delay)
                else:
                    print("Max retries reached, skipping test case")
                    return None
        
        return None
    
    async def run_evaluation(self):
        """Run evaluation on all test cases."""
        # Setup evaluation environment
        await self.setup()
        
        # Get test cases
        test_cases = self.get_test_cases()
        
        # Process each test case
        results = []
        for test_case in test_cases:
            try:
                # Wait for rate limit
                await self._wait_for_rate_limit()
                
                # Process test case
                result = await self._process_test_case(test_case)
                results.append(result)
                
                # Update last API call time
                self.last_api_call = time.time()
            except Exception as e:
                print(f"Error processing test case: {e}")
                results.append({"error": str(e)})
        
        return results

    def get_test_cases(self) -> List[ConversationalTestCase]:
        """Get test cases for this evaluation suite."""
        return self.create_test_cases()

async def run_evaluation_suite(suite_class: Type[EvaluationSuite], context: RouterContext) -> Dict[str, Any]:
    """Run a specific evaluation suite."""
    suite = suite_class(context)
    return await suite.run_evaluation() 