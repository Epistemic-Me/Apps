"""
BioAge Score evaluation suite for testing the BioAgeScore conversation module.
"""

from typing import List, Dict, Any
from deepeval.test_case import ConversationalTestCase, LLMTestCase, LLMTestCaseParams
from deepeval.metrics import ConversationalGEval
from deepeval import evaluate
from evaluations.framework import EvaluationSuite, RouterContext
import os
import asyncio
import json
from datetime import datetime, timedelta
import random
from bio_age_coach.mcp.modules.bio_age_score_module import BioAgeScoreModule
from bio_age_coach.mcp.utils.client import MultiServerMCPClient
from bio_age_coach.mcp.servers.health_server import HealthServer
from bio_age_coach.mcp.servers.research_server import ResearchServer
from bio_age_coach.mcp.servers.tools_server import ToolsServer
from bio_age_coach.mcp.servers.bio_age_score_server import BioAgeScoreServer

class SetupError(Exception):
    """Error raised during test setup."""
    pass

# Configure Confident AI tracking
os.environ["DEEPEVAL_API_KEY"] = os.getenv("CONFIDENT_AI_KEY", "")
os.environ["DEEPEVAL_DATASET_NAME"] = "bio_age_score_evaluation"
os.environ["DEEPEVAL_EXPERIMENT_NAME"] = "bio_age_coach_responses"

class BioAgeScoreEvaluation(EvaluationSuite):
    """Evaluation suite for BioAge Score functionality."""
    
    def _initialize_metrics(self):
        """Initialize evaluation metrics."""
        self.knowledge_retention = ConversationalGEval(
            name="Knowledge Retention",
            criteria="""Given the 'actual output' are generated responses from the Bio Age Coach
            and 'input' are user queries, determine whether the chatbot consistently maintains
            accurate information about bio-age scores across the entire conversation. Check if:
            1. Score values remain consistent when referenced multiple times
            2. Health metrics and their interpretations are consistent
            3. Recommendations align with previously mentioned health data""",
            evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.INPUT],
            threshold=0.7
        )
        
        self.conversation_relevancy = ConversationalGEval(
            name="Conversation Relevancy",
            criteria="""Given the 'actual output' are generated responses from the Bio Age Coach
            and 'input' are user queries about bio-age scores, determine whether each response
            directly addresses the user's query while maintaining context from previous turns.
            The chatbot should:
            1. Answer the immediate question
            2. Reference relevant information from previous turns
            3. Maintain focus on bio-age score topics""",
            evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.INPUT],
            threshold=0.7
        )
        
        self.conversation_completeness = ConversationalGEval(
            name="Conversation Completeness",
            criteria="""Given the 'actual output' are generated responses from the Bio Age Coach
            and 'expected output' are ideal responses, determine whether the conversation provides
            comprehensive information about bio-age scores throughout the interaction. Evaluate if:
            1. All components of the bio-age score are explained
            2. Health data interpretations are thorough
            3. Recommendations are specific and actionable
            4. Follow-up questions are anticipated and addressed""",
            evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.EXPECTED_OUTPUT],
            threshold=0.7
        )
    
    async def setup(self) -> None:
        """Set up the test environment."""
        try:
            # Initialize metrics
            self._initialize_metrics()
            
            # Get health server
            health_server = self.context.mcp_client.servers.get("health")
            if not health_server:
                raise ValueError("Health server not found in MCP client")
                
            # Process health data from test directory
            test_data_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "test_health_data"))
            print(f"Looking for test data in: {test_data_path}")
            health_server.test_data_path = test_data_path
            await health_server._process_apple_health_data()
            
            # Get processed health data
            health_data_response = await health_server.handle_request({
                "type": "metrics",
                "timeframe": "30D",
                "api_key": os.getenv("OPENAI_API_KEY")
            })
            
            if "error" in health_data_response:
                raise ValueError(f"Failed to get health data: {health_data_response['error']}")
                
            # Create and initialize module
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable is not set")
            
            self.module = BioAgeScoreModule(api_key, self.context.mcp_client)
            
            # Initialize module with processed health data
            await self.module.initialize({
                "user_id": "test_user",
                "health_data": health_data_response.get("metrics", {}),
                "habits": {
                    "sleep": ["Regular 11pm bedtime", "No screens after 10pm"],
                    "exercise": ["Morning workouts", "Weekend hiking"],
                    "movement": ["Standing desk", "Walking meetings"]
                }
            })
            
        except Exception as e:
            raise SetupError(f"Setup error: {str(e)}")
        
    def _generate_test_data(self) -> Dict[str, Any]:
        """Generate realistic test data with various patterns."""
        today = datetime.now()
        data_series = []
        
        # Define patterns for more realistic data
        patterns = [
            {"name": "consistent", "sleep": (7.5, 8.5), "calories": (400, 600), "steps": (9000, 11000)},
            {"name": "improving", "sleep": (6.0, 8.0), "calories": (300, 700), "steps": (7000, 12000)},
            {"name": "declining", "sleep": (8.0, 6.0), "calories": (600, 300), "steps": (11000, 7000)},
            {"name": "weekend_dip", "sleep": [(7.5, 8.5), (6.0, 7.0)], "calories": [(500, 600), (300, 400)], "steps": [(10000, 11000), (6000, 7000)]}
        ]
        
        # Generate 30 days of data with patterns
        for i in range(30):
            date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            pattern = patterns[i % len(patterns)]
            
            # Apply pattern with some randomness
            if isinstance(pattern["sleep"], tuple):
                sleep_range = pattern["sleep"]
                calories_range = pattern["calories"]
                steps_range = pattern["steps"]
            else:
                # Weekend pattern
                is_weekend = i % 7 >= 5
                idx = 1 if is_weekend else 0
                sleep_range = pattern["sleep"][idx]
                calories_range = pattern["calories"][idx]
                steps_range = pattern["steps"][idx]
            
            daily_data = {
                "date": date,
                "sleep_hours": round(random.uniform(*sleep_range), 1),
                "active_calories": round(random.uniform(*calories_range)),
                "steps": round(random.uniform(*steps_range)),
                "active_minutes": round(random.uniform(30, 60))
            }
            data_series.append(daily_data)
        
        return {
            "user_id": "test_user_123",
            "data_series": data_series
        }
        
    def _generate_test_habits(self) -> Dict[str, Any]:
        """Generate test habits data."""
        return {
            "sleep": {
                "bedtime": "22:00",
                "wake_time": "06:00",
                "quality": "good",
                "routine": "reading before bed",
                "barriers": ["screen time", "late work"]
            },
            "exercise": {
                "preferred_time": "morning",
                "activities": ["walking", "cycling", "yoga"],
                "barriers": ["busy schedule", "weather"],
                "goals": ["increase strength", "improve endurance"]
            },
            "lifestyle": {
                "stress_level": "moderate",
                "work_schedule": "9-5",
                "commute": "30 minutes",
                "diet_quality": "balanced"
            }
        }
        
    def _generate_test_plan(self) -> Dict[str, Any]:
        """Generate test improvement plan."""
        return {
            "sleep_goal": {
                "target": "8 hours",
                "steps": [
                    "set consistent bedtime",
                    "create bedtime routine",
                    "limit screen time"
                ],
                "tracking": "sleep duration and quality",
                "timeline": "4 weeks"
            },
            "exercise_goal": {
                "target": "500 active calories",
                "steps": [
                    "morning workout routine",
                    "lunchtime walk",
                    "evening yoga"
                ],
                "tracking": "daily active calories",
                "timeline": "6 weeks"
            },
            "steps_goal": {
                "target": "10000 steps",
                "steps": [
                    "take stairs",
                    "walking meetings",
                    "evening walk"
                ],
                "tracking": "daily step count",
                "timeline": "4 weeks"
            }
        }
    
    def create_test_cases(self) -> List[ConversationalTestCase]:
        """Create comprehensive test cases for BioAge Score functionality."""
        base_context = [
            "User Demographics: Adult individual",
            "Data Available: 30 days of health metrics",
            "Health Metrics: Sleep duration (7-9 hours), active calories (300-500), steps (8000-12000)",
            "Score Components: Sleep (60 pts max), Exercise (30 pts max), Steps (30 pts max)",
            "Clinical Guidelines: Sleep Foundation, WHO Physical Activity Guidelines",
            "Safety Considerations: No reported health issues"
        ]
        
        scientific_context = [
            "Evidence Base:",
            "- Sleep: 7-9 hours optimal for adults (Sleep Foundation, 2024)",
            "- Physical Activity: 150-300 minutes/week moderate intensity (WHO, 2024)",
            "- Steps: 7,000-10,000 daily steps associated with longevity (JAMA, 2023)",
            "Bio-Age Impact:",
            "- Quality sleep reduces biological age by 2-3 years",
            "- Regular exercise can lower biological age by 4-5 years",
            "- Consistent movement throughout day optimizes cellular health"
        ]
        
        base_context.extend(scientific_context)
        
        test_cases = []
        
        # Test Case 1: Current Score with Knowledge Retention
        initial_turn = LLMTestCase(
            input="Can you help me understand my bio-age score?",
            actual_output=None,
            expected_output="I'll help you understand your BioAge Score, which measures how your lifestyle impacts your biological age. Would you like to see your current score and what it means?",
            context=base_context
        )
        
        follow_up_turn = LLMTestCase(
            input="Yes, what is my current score and what does it mean?",
            actual_output=None,
            expected_output="""Based on your recent health data, here's your bio-age score analysis:

📊 Current Score: 85/120 points
- Sleep Component: 55/60 (Very Good)
- Exercise Component: 25/30 (Good)
- Movement Component: 28/30 (Excellent)

This translates to a biological age approximately 2.5 years below your chronological age. Your consistent sleep schedule and regular movement are key contributors to this positive outcome.

Would you like to explore specific strategies to optimize your score further?""",
            context=base_context
        )
        
        test_cases.append(
            ConversationalTestCase(
                turns=[initial_turn, follow_up_turn],
                chatbot_role="Bio Age Coach"
            )
        )
        
        # Test Case 2: Score Change with Trend Analysis
        initial_turn = LLMTestCase(
            input="How has my bio-age score been changing?",
            actual_output=None,
            expected_output="I'll analyze your bio-age score trends over time. Let me gather that data for you.",
            context=base_context
        )
        
        follow_up_turn = LLMTestCase(
            input="What are the specific changes over the past month?",
            actual_output=None,
            expected_output="""Here's your 30-day bio-age score trend analysis:

📈 Score Progression:
- Starting Score: 78/120
- Current Score: 85/120
- Net Improvement: +7 points

Component Trends:
1. Sleep (Improving):
   - More consistent bedtime
   - Average duration increased by 30 minutes

2. Exercise (Stable):
   - Maintaining regular activity
   - Consistent morning workouts

3. Movement (Improving):
   - Step count up by 1,500/day
   - Better daily distribution

Would you like to see a detailed breakdown of any component?""",
            context=base_context
        )
        
        test_cases.append(
            ConversationalTestCase(
                turns=[initial_turn, follow_up_turn],
                chatbot_role="Bio Age Coach"
            )
        )
        
        # Test Case 3: Improvement Actions with Personalization
        initial_turn = LLMTestCase(
            input="I'd like to improve my bio-age score. Can you help?",
            actual_output=None,
            expected_output="I'll analyze your current metrics and create a personalized plan to help you optimize your bio-age score. Let me look at your data and identify the most impactful opportunities for improvement.",
            context=base_context
        )
        
        follow_up_turn = LLMTestCase(
            input="What specific actions should I take to improve my score?",
            actual_output=None,
            expected_output="""Based on your current metrics, here are targeted recommendations to improve your bio-age score:

1. Sleep Optimization (+5 points potential):
   ✓ Move bedtime 30 minutes earlier (22:00)
   ✓ Implement 15-min pre-bed meditation
   ✓ Reduce evening screen time

2. Exercise Enhancement (+5 points potential):
   ✓ Add 2 HIIT sessions per week
   ✓ Increase workout duration to 45 mins
   ✓ Include strength training

3. Movement Optimization (+2 points potential):
   ✓ Add movement breaks every 2 hours
   ✓ Take walking meetings
   ✓ Use stairs instead of elevator

Would you like a detailed plan for implementing any of these recommendations?""",
            context=base_context
        )
        
        test_cases.append(
            ConversationalTestCase(
                turns=[initial_turn, follow_up_turn],
                chatbot_role="Bio Age Coach"
            )
        )
        
        return test_cases
    
    async def run_evaluation(self) -> List[ConversationalTestCase]:
        """Run the evaluation with metrics."""
        test_cases = self.get_test_cases()
        
        for test_case in test_cases:
            # Process each turn in the conversation
            for turn in test_case.turns:
                # Process the request
                response = await self.module._process_request({
                    "message": turn.input,
                    "conversation_history": [t.input for t in test_case.turns]
                })
                turn.actual_output = response.get("response", "")
            
            # Evaluate the test case with metrics
            self.knowledge_retention.measure(test_case)
            self.conversation_relevancy.measure(test_case)
            self.conversation_completeness.measure(test_case)
        
        return test_cases

async def main():
    """Run the BioAge Score evaluation suite."""
    try:
        # Initialize MCP client
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
            
        # Initialize MCP client and servers
        mcp_client = MultiServerMCPClient()
        
        # Initialize and register servers
        health_server = HealthServer(api_key)
        research_server = ResearchServer(api_key)
        tools_server = ToolsServer(api_key)
        bio_age_score_server = BioAgeScoreServer(api_key)
        
        # Register servers with specific types that match module expectations
        mcp_client.register_server("health", health_server)
        mcp_client.register_server("research", research_server)
        mcp_client.register_server("tools", tools_server)
        mcp_client.register_server("bio_age_score", bio_age_score_server)
        
        # Initialize test data for each server
        test_data = {
            "user_id": "test_user_123",
            "api_key": api_key
        }
        
        for server in [health_server, research_server, tools_server, bio_age_score_server]:
            await server.initialize_data(test_data)
        
        # Create context with MCP client
        context = RouterContext(mcp_client=mcp_client)
        
        # Create and run evaluation
        evaluation = BioAgeScoreEvaluation(context)
        await evaluation.setup()
        results = await evaluation.run_evaluation()
        
        print("\nBioAge Score Module Evaluation Results:")
        print("=" * 50)
        
        # Process results
        successful_tests = 0
        failed_tests = 0
        
        for i, result in enumerate(results, 1):
            print(f"\nTest Case {i}:")
            if result and isinstance(result, ConversationalTestCase):
                successful_tests += 1
                last_turn = result.turns[-1]
                print(f"✓ Input: {last_turn.input}")
                print(f"✓ Expected Output: {last_turn.expected_output}")
                print(f"✓ Actual Output: {last_turn.actual_output}")
                
                # Print tool chain verification if available
                if hasattr(last_turn, 'tools_called') and last_turn.tools_called:
                    print("\nTool Chain:")
                    for tool in last_turn.tools_called:
                        print(f"  ➜ {tool.name}")
                        print(f"    Args: {json.dumps(tool.args, indent=4)}")
                        print(f"    Response: {json.dumps(tool.response, indent=4)}")
            else:
                failed_tests += 1
                print("✗ Test case failed to process")
        
        # Print summary with clear formatting
        print("\nEvaluation Summary:")
        print("=" * 50)
        print(f"Total Test Cases: {len(results)}")
        print(f"✓ Successful Tests: {successful_tests}")
        print(f"✗ Failed Tests: {failed_tests}")
        
        if failed_tests > 0:
            print("\nWarning: Some tests failed. Please check the output above for details.")
        
    except Exception as e:
        print(f"Error running BioAge Score evaluation: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 