"""
MCP-specific evaluations for testing server integration and routing.
"""

import os
from typing import Dict, List, Any
from dataclasses import dataclass
from deepeval import evaluate
from deepeval.test_case import LLMTestCase
from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric
from bio_age_coach.mcp.client import MultiServerMCPClient
from bio_age_coach.mcp.router import QueryRouter
from .test_data import create_test_data, create_variant_test_data, DataCategory

@dataclass
class MCPTestCase:
    """Test case for MCP routing and processing."""
    query: str
    expected_server: str
    expected_insights: List[str]
    expected_response: str
    test_data_variants: Dict[DataCategory, Dict[str, Any]] = None

def create_mcp_test_cases() -> List[MCPTestCase]:
    """Create test cases for MCP routing and processing."""
    return [
        MCPTestCase(
            query="What does my HbA1c of 5.9% indicate about my metabolic health?",
            expected_server="health",
            expected_insights=[
                "HbA1c ranges: Normal < 5.7%, Prediabetic 5.7-6.4%, Diabetic > 6.4%",
                "Elevated HbA1c indicates higher average blood sugar over past 3 months",
                "Prediabetic range suggests increased risk of metabolic issues"
            ],
            expected_response="Your HbA1c of 5.9% falls in the prediabetic range..."
        ),
        MCPTestCase(
            query="What's the latest research on grip strength and longevity?",
            expected_server="research",
            expected_insights=[
                "Strong correlation between grip strength and overall mortality",
                "Grip strength is a reliable predictor of functional capacity",
                "Age-specific grip strength standards provide context for assessment"
            ],
            expected_response="Recent research shows that grip strength is a powerful predictor..."
        ),
        MCPTestCase(
            query="Calculate my biological age based on my metrics",
            expected_server="tools",
            expected_insights=[
                "Multiple factors contribute to biological age calculation",
                "Weighting of different biomarkers in age assessment",
                "Importance of both functional and biochemical markers"
            ],
            expected_response="Based on your comprehensive metrics..."
        )
    ]

async def run_mcp_evaluation(mcp_client: MultiServerMCPClient, query_router: QueryRouter):
    """Run MCP-specific evaluations."""
    test_cases = create_mcp_test_cases()
    processed_cases = []

    for test_case in test_cases:
        # Set up test data variants if specified
        if test_case.test_data_variants:
            test_data = create_test_data()
            for category, overrides in test_case.test_data_variants.items():
                variant_data = create_variant_test_data(category, **overrides)
                test_data[category.value].update(variant_data[category.value])
        else:
            test_data = create_test_data()

        try:
            # Route the query
            routed_server = await query_router.route_query(test_case.query)
            
            # Verify routing
            if routed_server != test_case.expected_server:
                print(f"❌ Routing mismatch for query: {test_case.query}")
                print(f"Expected: {test_case.expected_server}, Got: {routed_server}")
                continue

            # Get server response
            response = await mcp_client.send_request(
                routed_server,
                {
                    "type": "query",
                    "query": test_case.query,
                    "data": test_data,
                    "api_key": os.getenv("OPENAI_API_KEY")
                }
            )

            # Create LLMTestCase for evaluation
            llm_test_case = LLMTestCase(
                input=test_case.query,
                actual_output=response.get("response", ""),
                expected_output=test_case.expected_response,
                retrieval_context=test_case.expected_insights
            )
            processed_cases.append(llm_test_case)

        except Exception as e:
            print(f"Error processing test case: {str(e)}")
            continue

    # Run evaluation with processed cases
    metrics = [
        AnswerRelevancyMetric(threshold=0.7),
        FaithfulnessMetric(threshold=0.7)
    ]

    results = evaluate(test_cases=processed_cases, metrics=metrics)

    # Print MCP-specific metrics
    print("\n=== MCP Evaluation Results ===")
    print(f"Total test cases: {len(test_cases)}")
    print(f"Successfully processed: {len(processed_cases)} of {len(test_cases)}")
    print("\nRouting Accuracy:")
    routing_accuracy = sum(1 for case in processed_cases if case.actual_output) / len(test_cases)
    print(f"- {routing_accuracy:.2%} queries routed correctly")

    return results 