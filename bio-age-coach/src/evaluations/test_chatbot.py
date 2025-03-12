"""
Test suite for Bio Age Coach chatbot.
"""

import os
import asyncio
from dotenv import load_dotenv
from deepeval import evaluate
from deepeval.test_case import LLMTestCase, LLMTestCaseParams
from evaluations.framework import EvaluationSuite, RouterContext
from bio_age_coach.mcp.health_server import HealthServer
from bio_age_coach.mcp.research_server import ResearchServer
from bio_age_coach.mcp.tools_server import ToolsServer
from bio_age_coach.mcp.client import MultiServerMCPClient
from bio_age_coach.mcp.router import QueryRouter
from bio_age_coach.chatbot.coach import BioAgeCoach
from typing import List, Dict, Any

class ChatbotEvaluationSuite(EvaluationSuite):
    """Test suite for Bio Age Coach with configurable router contexts."""
    
    def __init__(self, context: RouterContext, test_config: Dict[str, Any] = None):
        """Initialize the test suite with a specific router context."""
        super().__init__(context)
        self.test_config = test_config or {}
        
    async def setup(self):
        """Setup test environment with specific server configuration."""
        # Initialize test data
        self.test_data = {
            "demographics": {
                "age": 35,
                "gender": "male",
                "height": 175,
                "weight": 70
            },
            "capabilities": ["walking", "light_exercise"],
            "biomarkers": {
                "glucose": 5.5,
                "hba1c": 5.2,
                "hdl": 1.4,
                "ldl": 2.8,
                "triglycerides": 1.2
            },
            "health_data": {
                "steps_per_day": 8000,
                "exercise_minutes": 30,
                "sleep_hours": 7
            }
        }
        
        # Initialize servers based on router context
        if self.context.health_server:
            await self.context.health_server.initialize_data({
                "health_metrics": self.test_data["health_data"],
                "biomarkers": self.test_data["biomarkers"]
            })
            
        if self.context.tools_server:
            await self.context.tools_server.initialize_data({
                "fitness_metrics": {
                    "capabilities": self.test_data["capabilities"]
                }
            })
            
        if self.context.research_server:
            await self.context.research_server.initialize_data({
                "papers": self.test_config.get("research_papers", []),
                "protocols": self.test_config.get("protocols", [])
            })
        
        # Initialize coach with context-specific configuration
        self.coach = BioAgeCoach(self.mcp_client, self.router, test_mode=False)
        await self.coach.initialize()
        self.coach.user_data = self.test_data

    def get_test_cases(self) -> List[LLMTestCase]:
        """Return test cases based on available servers in the context."""
        test_cases = []
        
        # Health server test cases
        if self.context.health_server:
            test_cases.extend([
                LLMTestCase(
                    input="What is my HbA1c level and what does it mean?",
                    actual_output=None,
                    expected_output="Your HbA1c level is 5.2%, which is within the healthy range (below 5.7%). This indicates good blood sugar control over the past 2-3 months.",
                    context=[f"User data: {self.test_data}"]
                ),
                LLMTestCase(
                    input="How is my cholesterol profile?",
                    actual_output=None,
                    expected_output="Your cholesterol profile is good. Your HDL (good cholesterol) is 1.4 mmol/L (healthy range >1.0), LDL (bad cholesterol) is 2.8 mmol/L (optimal <3.0), and triglycerides are 1.2 mmol/L (normal <1.7).",
                    context=[f"User data: {self.test_data}"]
                )
            ])
            
        # Tools server test cases for fitness metrics
        if self.context.tools_server:
            fitness_config = self.test_config.get("fitness_metrics", {})
            health_data = self.test_config.get("health_data", {})
            
            test_cases.extend([
                LLMTestCase(
                    input="What is my current fitness level based on my capabilities and metrics?",
                    actual_output=None,
                    expected_output=(
                        "Based on your metrics:\n"
                        "1. Cardio fitness: VO2 max of 35.5 indicates moderate cardiovascular fitness\n"
                        "2. Strength: 20 push-ups and grip strength of 85kg show good muscular strength\n"
                        "3. Activity: You average 8,000 steps and 30 minutes of exercise daily\n"
                        "Your fitness level is moderate with good strength indicators. There's room for improvement in cardiovascular fitness."
                    ),
                    context=[f"Fitness data: {fitness_config}, Health data: {health_data}"]
                ),
                LLMTestCase(
                    input="What exercise recommendations do you have based on my current capabilities?",
                    actual_output=None,
                    expected_output=(
                        "Based on your capabilities (walking, light exercise, jogging, strength training) and current metrics, I recommend:\n"
                        "1. Gradually increase your daily steps from 8,000 to 10,000\n"
                        "2. Progress from 30 to 45 minutes of exercise at moderate intensity (heart rate 120-150)\n"
                        "3. Incorporate 2-3 strength training sessions per week to maintain and improve your current strength levels\n"
                        "4. Add 1-2 jogging sessions to improve your VO2 max"
                    ),
                    context=[f"Fitness data: {fitness_config}, Health data: {health_data}"]
                ),
                LLMTestCase(
                    input="How can I improve my cardiovascular fitness based on my current metrics?",
                    actual_output=None,
                    expected_output=(
                        "To improve your cardiovascular fitness from your current VO2 max of 35.5:\n"
                        "1. Increase moderate-intensity exercise (heart rate 120-150) duration from 30 to 45 minutes\n"
                        "2. Add 2 high-intensity intervals (heart rate >150) sessions per week\n"
                        "3. Maintain consistent activity with 8,000+ daily steps\n"
                        "4. Gradually progress jogging duration and intensity"
                    ),
                    context=[f"Fitness data: {fitness_config}, Health data: {health_data}"]
                ),
                LLMTestCase(
                    input="What are my current heart rate zones and how should I use them in training?",
                    actual_output=None,
                    expected_output=(
                        "Your heart rate zones are:\n"
                        "- Low intensity: around 60 bpm (recovery, warm-up)\n"
                        "- Moderate intensity: around 120 bpm (aerobic training)\n"
                        "- High intensity: around 150 bpm (anaerobic training)\n"
                        "For optimal training: Start with 5-10 minutes in low zone for warm-up, maintain moderate zone for 20-30 minutes for endurance, and include short intervals (1-3 minutes) in high zone for cardiovascular improvement."
                    ),
                    context=[f"Fitness data: {fitness_config}, Health data: {health_data}"]
                )
            ])
            
        # Research server test cases
        if self.context.research_server:
            test_cases.append(
                LLMTestCase(
                    input="What does research say about the relationship between HbA1c and biological age?",
                    actual_output=None,
                    expected_output="Based on current research, HbA1c levels have a significant correlation with biological age. Studies show that maintaining HbA1c below 5.7% is associated with better aging outcomes.",
                    context=[f"User data: {self.test_data}"]
                )
            )
            
        return test_cases

    async def _process_test_case(self, test_case: LLMTestCase):
        """Process a single test case with error handling for server-specific issues."""
        try:
            # Get response from coach
            response = await self.coach.process_message(test_case.input)
            test_case.actual_output = response
            
            # Run evaluation using DeepEval
            results = evaluate(
                test_cases=[test_case],
                metrics=self.metrics
            )
            
            return {
                "input": test_case.input,
                "expected": test_case.expected_output,
                "actual": test_case.actual_output,
                "results": results.to_dict() if hasattr(results, 'to_dict') else str(results)
            }
            
        except Exception as e:
            print(f"Error processing test case: {e}")
            return None

async def main():
    """Main function to run evaluation with different router contexts."""
    # Load environment variables
    load_dotenv()
    
    # Ensure OpenAI API key is set
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")
    
    # Initialize all possible servers
    health_server = HealthServer(api_key)
    research_server = ResearchServer(api_key)
    tools_server = ToolsServer(api_key)
    
    # Define test configurations for different contexts
    test_configs = {
        "fitness_metrics": {
            "context": RouterContext(
                tools_server=tools_server,
                health_server=health_server  # Need health server for basic metrics
            ),
            "config": {
                "fitness_metrics": {
                    "capabilities": [
                        "walking",
                        "light_exercise",
                        "jogging",
                        "strength_training"
                    ],
                    "metrics": {
                        "vo2_max": 35.5,
                        "resting_heart_rate": 65,
                        "push_ups": 20,
                        "grip_strength": 85
                    }
                },
                "health_data": {
                    "steps_per_day": 8000,
                    "exercise_minutes": 30,
                    "active_minutes": 45,
                    "heart_rate_zones": {
                        "low": 60,
                        "moderate": 120,
                        "high": 150
                    }
                }
            }
        }
    }
    
    # Run evaluations for each context
    for context_name, config in test_configs.items():
        print(f"\nTesting {context_name} configuration:")
        print("=" * 50)
        
        context = config["context"]
        test_config = config["config"]
        
        # Create MCP client and query router for this context
        mcp_client = MultiServerMCPClient(
            health_server=context.health_server,
            research_server=context.research_server,
            tools_server=context.tools_server
        )
        query_router = QueryRouter(
            health_server=context.health_server,
            research_server=context.research_server,
            tools_server=context.tools_server
        )
        
        # Setup context
        context.mcp_client = mcp_client
        context.router = query_router
        
        # Run evaluation
        try:
            results = await ChatbotEvaluationSuite(context, test_config).run_evaluation()
            print(f"\nEvaluation Results for {context_name}:")
            for result in results:
                if result:
                    print(f"\nInput: {result['input']}")
                    print(f"Expected: {result['expected']}")
                    print(f"Actual: {result['actual']}")
                    print("Metrics:")
                    if isinstance(result['results'], dict):
                        for metric_name, metric_result in result['results'].items():
                            print(f"{metric_name}: {metric_result}")
                    else:
                        print(result['results'])
                else:
                    print("Test case failed to process")
        except Exception as e:
            print(f"Error running evaluation for {context_name}: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 