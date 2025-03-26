"""Integration tests for coaching sessions."""

import asyncio
import logging
import os
from pathlib import Path
from typing import Any, Dict

import pytest
from deepeval import evaluate as deepeval_evaluate
from deepeval.metrics import ConversationalGEval
from deepeval.test_case import (
    ConversationalTestCase,
    LLMTestCase,
    LLMTestCaseParams
)

from bio_age_coach.agents.factory import create_agents
from bio_age_coach.chatbot.coach import BioAgeCoach
from bio_age_coach.mcp.client import MultiServerMCPClient
from bio_age_coach.mcp.servers.bio_age_score_server import BioAgeScoreServer
from bio_age_coach.mcp.servers.health_server import HealthServer
from bio_age_coach.mcp.servers.research_server import ResearchServer
from bio_age_coach.mcp.servers.tools_server import ToolsServer
from bio_age_coach.router.router_adapter import RouterAdapter
from bio_age_coach.router.semantic_router import SemanticRouter
from bio_age_coach.tests.evaluation_datasets.bio_age_score_dataset import (
    BioAgeScoreDatasetGenerator,
    generate_bio_age_score_dataset
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest.fixture
async def test_dataset():
    """Load or generate the test dataset."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set")
    
    generator = BioAgeScoreDatasetGenerator(api_key)
    
    try:
        logger.info("Attempting to load existing dataset...")
        dataset = generator.load_dataset()
        logger.info("Successfully loaded existing dataset")
    except FileNotFoundError:
        logger.info("No existing dataset found, generating new dataset...")
        try:
            dataset = await generate_bio_age_score_dataset(api_key)
            logger.info("Successfully generated new dataset")
        except Exception as e:
            logger.error(f"Failed to generate dataset: {str(e)}")
            raise
    
    if not dataset or not dataset.test_cases:
        pytest.fail("Dataset is empty or invalid")
    
    return dataset

@pytest.fixture
async def test_setup():
    """Set up test environment with MCP servers and client."""
    # Initialize environment variables
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set")

    # Get absolute paths using pathlib
    current_dir = Path(__file__).parent
    project_root = current_dir.parents[4]  # Go up 4 levels to reach project root
    papers_dir = project_root / "data" / "papers"
    test_data_path = project_root / "data" / "test_health_data"

    logger.info(f"Papers directory: {papers_dir}")
    logger.info(f"Test data path: {test_data_path}")

    if not test_data_path.exists():
        pytest.fail(f"Test data directory not found at {test_data_path}")

    # Initialize test users
    test_users = [
        {"id": "test_user_1", "username": "Test User 1"}
    ]

    try:
        # Create MCP client
        mcp_client = MultiServerMCPClient(api_key=api_key)

        # Initialize servers
        health_server = HealthServer(api_key)
        await health_server.initialize_data({
            "test_data_path": str(test_data_path),
            "users": test_users,
            "process_test_data": True
        })

        research_server = ResearchServer(api_key, str(papers_dir))
        tools_server = ToolsServer(api_key)
        bio_age_score_server = BioAgeScoreServer(api_key)

        # Register servers with MCP client
        await mcp_client.add_server("health", health_server)
        await mcp_client.add_server("research", research_server)
        await mcp_client.add_server("tools", tools_server)
        await mcp_client.add_server("bio_age_score", bio_age_score_server)

        # Create agents and router components
        agents = create_agents(api_key, mcp_client)
        semantic_router = SemanticRouter(api_key=api_key, agents=agents)
        router_adapter = RouterAdapter(
            semantic_router=semantic_router,
            mcp_client=mcp_client
        )
        coach = await BioAgeCoach.create(mcp_client, router_adapter)

        return mcp_client, router_adapter, coach, semantic_router, agents
    except Exception as e:
        logger.error(f"Failed to set up test environment: {str(e)}")
        raise

class TestSession:
    """Test session class to manage test state and dataset updates."""
    
    evaluation_cache = {}  # Class-level cache for evaluation results
    
    def __init__(self, dataset_generator: BioAgeScoreDatasetGenerator, test_setup: tuple):
        """Initialize test session.
        
        Args:
            dataset_generator: Generator for test cases
            test_setup: Tuple of (mcp_client, router_adapter, coach, semantic_router, agents)
        """
        self.dataset_generator = dataset_generator
        self.contexts = []  # Store contexts from test runs
        self.mcp_client, self.router_adapter, _, _, _ = test_setup
        self.saved_test_cases = []  # Track test cases that have been saved
        
    def add_context(self, context: Dict[str, Any]):
        """Add a context from a test run."""
        self.contexts.append(context)
        
    async def update_dataset_with_passing_result(self, test_case: ConversationalTestCase):
        """Update dataset with a passing test case and track it.
        
        Args:
            test_case: The passing test case to add to the dataset
        """
        try:
            await self.dataset_generator.update_dataset_with_passing_result(test_case)
            self.saved_test_cases.append({
                'input': test_case.turns[0].input,
                'context': test_case.turns[0].context
            })
            logger.info(f"Successfully tracked saved test case: {test_case.turns[0].input}")
        except Exception as e:
            logger.error(f"Failed to save test case: {str(e)}")
            raise
        
    async def synthesize_new_test_cases(self) -> None:
        """Synthesize new test cases from accumulated contexts."""
        logger.info(f"Starting synthesis of new test cases from {len(self.contexts)} contexts")
        
        # Only synthesize from a maximum of 2 contexts to reduce API calls
        for context in self.contexts[:2]:
            try:
                new_test_case = await self.dataset_generator.synthesize_new_test_case(context)
                if new_test_case:
                    # Run the new test case
                    passed = await run_test_case(
                        new_test_case,
                        context,
                        self.mcp_client,
                        self.router_adapter
                    )
                    
                    if passed:
                        await self.update_dataset_with_passing_result(new_test_case)
                        logger.info("Successfully synthesized and saved new test case")
                    else:
                        logger.warning("Synthesized test case failed evaluation")
                else:
                    logger.warning("Failed to synthesize new test case")
            except Exception as e:
                logger.error(f"Error during test case synthesis and execution: {str(e)}")
        
        logger.info(f"Completed test case synthesis. Total saved test cases: {len(self.saved_test_cases)}")

    async def verify_saved_test_cases(self) -> bool:
        """Verify that test cases were properly saved to the dataset.
        
        Returns:
            bool: True if verification passes, False otherwise
        """
        try:
            # Load the current dataset
            dataset = self.dataset_generator.load_dataset()
            
            # Check if all saved test cases are in the dataset
            for saved_case in self.saved_test_cases:
                found = False
                for test_case in dataset.test_cases:
                    if (test_case.turns[0].input == saved_case['input'] and 
                        test_case.turns[0].context == saved_case['context']):
                        found = True
                        break
                
                if not found:
                    logger.error(f"Test case not found in dataset: {saved_case['input']}")
                    return False
            
            logger.info(f"Successfully verified {len(self.saved_test_cases)} test cases in dataset")
            return True
        except Exception as e:
            logger.error(f"Error verifying saved test cases: {str(e)}")
            return False

@pytest.fixture
async def test_session(test_setup, api_key):
    """Create a test session."""
    generator = BioAgeScoreDatasetGenerator(api_key)
    return TestSession(generator, test_setup)

async def run_test_case(
    test_case: ConversationalTestCase,
    context: Dict[str, Any],
    mcp_client: MultiServerMCPClient,
    router_adapter: RouterAdapter
) -> bool:
    """Run a single test case and return whether it passed."""
    try:
        # Initialize coach with context
        coach = await BioAgeCoach.create(mcp_client, router_adapter)
        await coach.update_context(context)  # Await the coroutine
        
        # Get response from coach
        response = await coach.handle_query(test_case.turns[0].input)
        
        # Format response
        formatted_response = format_coach_response(response)
        
        # Update test case with actual output
        test_case.turns[0].actual_output = formatted_response
        
        # Check cache for similar responses to avoid redundant evaluations
        cache_key = hash(formatted_response[:100])  # Use first 100 chars as cache key
        if cache_key in TestSession.evaluation_cache:
            test_case.turns[0].metrics_score = TestSession.evaluation_cache[cache_key]
            return True
        
        # Run assertions
        metrics = ConversationalGEval(
            name="Bio Age Coach Response Quality",
            criteria="""Given the 'actual output' are generated responses from a Bio Age Coach chatbot and 'input' are user queries to the chatbot, determine whether:
            1. The response is clear and well-structured
            2. The recommendations are specific and actionable
            3. The metrics and scores are explained clearly
            4. The language is professional and encouraging""",
            evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT],
            threshold=0.7,
            model="gpt-4o"
        )
        
        result = deepeval_evaluate(test_cases=[test_case], metrics=[metrics])
        # Check if any metrics failed and print their reasons
        for test_result in result.test_results:
            for metric_data in test_result.metrics_data:
                if not metric_data.success:
                    print(f"Failed metric: {metric_data.name}")
                    print(f"Score: {metric_data.score}")
                    print(f"Reason: {metric_data.reason}")
                    print(f"Error: {metric_data.error}")
                assert metric_data.success, f"Response quality check failed: {metric_data.reason}"
        
        return True
    except Exception as e:
        logging.error(f"Test case failed: {str(e)}")
        return False

@pytest.fixture
def api_key():
    """Get API key from environment."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set")
    return api_key

@pytest.mark.asyncio
async def test_full_coaching_session(test_setup, test_session):
    """Test a full coaching session with data upload and context updates."""
    mcp_client, router_adapter, coach, semantic_router, agents = test_setup
    
    # Set the user ID for the coach
    coach.user_id = "test_user_1"
    
    # Initialize base context
    base_context = [
        "User Demographics: Adult individual",
        "Data Available: 30 days of health metrics",
        "Health Metrics: Sleep duration (7-9 hours), active calories (300-500), steps (8000-12000)",
        "Score Components: Sleep (60 pts max), Exercise (30 pts max), Steps (30 pts max)",
        "Clinical Guidelines: Sleep Foundation, WHO Physical Activity Guidelines",
        "Safety Considerations: No reported health issues"
    ]
    
    # Test data with realistic patterns
    health_data = {
        "sleep_hours": 7.5,
        "active_calories": 500,
        "steps": 8000,
        "blood_pressure": "120/80",
        "resting_heart_rate": 65,
        "sleep_quality": "good",
        "stress_level": "moderate",
        "deep_sleep": 1.2,
        "rem_sleep": 2.0,
        "light_sleep": 4.3,
        "exercise_minutes": 45
    }
    
    # Format data upload metadata with proper nesting
    data_upload_metadata = {
        "data_upload": True,
        "data_type": "health",
        "data": {
            "health_data": [health_data]  # Format as a list of records
        }
    }
    
    # Upload health data with proper metadata
    print("\nUploading health data...")
    response = await coach.handle_data_upload(
        data_type="health",
        data=data_upload_metadata["data"],
        metadata=data_upload_metadata
    )
    
    # Print observation contexts after data upload
    print("\nObservation contexts after health data upload:")
    for agent_name, context in semantic_router.observation_contexts.get("test_user_1", {}).items():
        print(f"Agent: {agent_name}")
        print(f"  Context type: {type(context).__name__}")
        print(f"  Data type: {context.data_type}")
    
    # Verify data upload response
    metrics = ConversationalGEval(
        name="Bio Age Coach Response Quality",
        criteria="""Given the 'actual output' are generated responses from a Bio Age Coach chatbot and 'input' are user queries to the chatbot, determine whether:
            1. The response is clear and well-structured
            2. The recommendations are specific and actionable
            3. The metrics and scores are explained clearly
            4. The language is professional and encouraging""",
        evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT],
        threshold=0.7,
        model="gpt-4o"
    )
    
    # Test multi-turn conversation with context retention
    conversation = [
        {
            "query": "I've uploaded my health data. What insights can you provide?",
            "response": response["response"],
            "expected_focus": ["sleep quality", "stress level", "activity level"],
            "expected_output": """Based on your health data, I can provide insights about your:
1. Sleep patterns (7.5 hours with good quality)
2. Physical activity (8000 steps, 500 calories)
3. Stress management (moderate level)
Would you like to explore any of these areas in detail?"""
        },
        {
            "query": "Tell me about my sleep patterns",
            "expected_focus": ["sleep duration", "sleep quality", "sleep stages"],
            "expected_output": """Your sleep data shows:
- Total sleep: 7.5 hours (within recommended 7-9 hours)
- Sleep quality: Good
- Sleep stages:
  • Deep sleep: 1.2 hours (16%)
  • REM sleep: 2.0 hours (27%)
  • Light sleep: 4.3 hours (57%)
This is a healthy distribution of sleep stages."""
        },
        {
            "query": "What about my exercise habits?",
            "expected_focus": ["steps", "calories", "exercise duration"],
            "expected_output": """Your exercise metrics indicate:
- Daily steps: 8,000 (approaching 10,000 goal)
- Active calories: 500 (good level)
- Exercise duration: 45 minutes
You're meeting WHO guidelines for physical activity."""
        }
    ]
    
    # Process each turn in the conversation
    for turn in conversation:
        # Route query through semantic router
        response = await semantic_router.route_query(
            user_id="test_user_1",
            query=turn["query"]
        )
        
        # Create test case for this turn
        test_case = ConversationalTestCase(
            turns=[
                LLMTestCase(
                    input=turn["query"],
                    actual_output=response["response"],
                    expected_output=turn["expected_output"],
                    context=base_context
                )
            ]
        )
        
        # Evaluate response quality
        result = deepeval_evaluate(test_cases=[test_case], metrics=[metrics])
        
        # Verify response addresses expected focus areas
        response_text = response["response"].lower()
        focus_areas_found = [
            focus for focus in turn["expected_focus"]
            if focus.lower() in response_text
        ]
        assert len(focus_areas_found) > 0, f"Response did not address expected focus areas: {turn['expected_focus']}"
        
        # Verify response quality meets threshold
        assert any(test_result.success for test_result in result.test_results), "Response quality check failed"
        
        # Save successful test case
        if any(test_result.success for test_result in result.test_results):
            await test_session.update_dataset_with_passing_result(test_case)
    
    # Verify observation contexts were created and maintained
    assert "test_user_1" in semantic_router.observation_contexts, "No observation contexts created for test user"
    assert len(semantic_router.observation_contexts["test_user_1"]) > 0, "No observation contexts found for test user"
    
    # Verify route history was updated
    assert len(semantic_router.route_history) > 0, "No route history entries found"
    assert "method" in semantic_router.route_history[-1], "Route history entry missing method"
    
    # Verify test cases were saved
    assert await test_session.verify_saved_test_cases(), "Failed to save test cases to dataset"

@pytest.mark.asyncio
async def test_interactive_coaching_session(test_setup, test_session):
    """Test an interactive coaching session with multiple queries."""
    mcp_client, router_adapter, coach, semantic_router, agents = test_setup
    
    # Set the user ID for the coach
    coach.user_id = "test_user_1"
    
    # Initialize base context
    base_context = [
        "User Demographics: Adult individual",
        "Data Available: 30 days of health metrics",
        "Health Metrics: Sleep duration (6-7 hours), active calories (200-400), steps (5000-7000)",
        "Score Components: Sleep (60 pts max), Exercise (30 pts max), Steps (30 pts max)",
        "Clinical Guidelines: Sleep Foundation, WHO Physical Activity Guidelines",
        "Safety Considerations: No reported health issues"
    ]
    
    # Test data with realistic patterns showing areas for improvement
    health_data = {
        "blood_pressure": "130/85",
        "resting_heart_rate": 75,
        "sleep_quality": "poor",
        "stress_level": "high",
        "sleep_hours": 6.0,
        "active_calories": 300,
        "steps": 5000,
        "deep_sleep": 0.8,
        "rem_sleep": 1.5,
        "light_sleep": 3.7,
        "exercise_minutes": 25
    }
    
    # Format data upload metadata with proper nesting
    data_upload_metadata = {
        "data_upload": True,
        "data_type": "health",
        "data": {
            "health_data": [health_data]  # Format as a list of records
        }
    }
    
    # Upload health data with proper metadata
    print("\nUploading health data...")
    response = await coach.handle_data_upload(
        data_type="health",
        data=data_upload_metadata["data"],
        metadata=data_upload_metadata
    )
    
    # Print observation contexts after data upload
    print("\nObservation contexts after health data upload:")
    for agent_name, context in semantic_router.observation_contexts.get("test_user_1", {}).items():
        print(f"Agent: {agent_name}")
        print(f"  Context type: {type(context).__name__}")
        print(f"  Data type: {context.data_type}")
    
    metrics = ConversationalGEval(
        name="Bio Age Coach Response Quality",
        criteria="""Given the 'actual output' are generated responses from a Bio Age Coach chatbot and 'input' are user queries to the chatbot, determine whether:
            1. The response is clear and well-structured
            2. The recommendations are specific and actionable
            3. The metrics and scores are explained clearly
            4. The language is professional and encouraging""",
        evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT],
        threshold=0.7,
        model="gpt-4o"
    )
    
    # Test multi-turn conversation with context retention
    conversation = [
        # Initial data assessment
        {
            "query": "I've uploaded my health data. What insights can you provide?",
            "response": response["response"],
            "expected_focus": ["sleep quality", "stress level", "activity level"],
            "expected_output": """Based on your health data, I notice several areas that need attention:
1. Sleep: You're getting 6 hours with poor quality
2. Physical activity: 5000 steps and 300 calories are below targets
3. Stress: Your high stress levels may be affecting other metrics
Would you like to create a plan to improve these areas?"""
        },
        # Explore current habits
        {
            "query": "What habits should I focus on improving first?",
            "expected_focus": ["sleep", "exercise", "stress"],
            "expected_output": """Let's prioritize your habits for maximum impact:
1. Sleep Improvement (Priority)
   - Current: 6 hours with poor quality
   - Goal: 7-8 hours with better quality
   - Impact: Better sleep will help manage stress and energy

2. Stress Management
   - Current: High stress levels
   - Goal: Develop stress reduction techniques
   - Impact: Lower stress improves sleep and motivation

3. Physical Activity
   - Current: 5000 steps, 25 minutes exercise
   - Goal: 7500 steps, 30+ minutes exercise
   - Impact: More activity helps both sleep and stress

Which area would you like to work on first?"""
        },
        # Understand sleep habits
        {
            "query": "I usually go to bed around midnight and wake up at 7am. Is that enough sleep?",
            "expected_focus": ["sleep duration", "sleep quality", "bedtime routine"],
            "expected_output": """Your current sleep schedule needs adjustment:
- 7 hours between bedtime and wake-up
- Actual sleep time: 6 hours (indicating sleep efficiency issues)
- Sleep stages are suboptimal:
  • Deep sleep: 0.8 hours (13%) - below ideal 15-20%
  • REM sleep: 1.5 hours (25%) - near ideal 20-25%
  • Light sleep: 3.7 hours (62%) - slightly high

Recommendations:
1. Try going to bed at 11pm instead of midnight
2. Aim for 8 hours in bed to get 7+ hours of actual sleep
3. Establish a wind-down routine starting at 10pm

Would you like specific tips for improving your bedtime routine?"""
        },
        # Exercise habits
        {
            "query": "I find it hard to exercise regularly due to my busy schedule. What do you suggest?",
            "expected_focus": ["time management", "exercise types", "activity scheduling"],
            "expected_output": """Let's work with your busy schedule to increase activity:

Current Activity:
- 25 minutes of exercise (below recommended 30-60 minutes)
- 5000 steps (below target 7500-10000)
- 300 active calories (below target 400-600)

Quick-Win Suggestions:
1. Time-Efficient Options:
   - 10-minute morning workout
   - Walking meetings
   - Desk exercises

2. Schedule Integration:
   - Park further from destinations
   - Take stairs instead of elevator
   - 5-minute movement breaks every hour

3. Progressive Goals:
   - Week 1: Add 1000 daily steps
   - Week 2: Include 2 10-minute workouts
   - Week 3: Extend to 15-minute sessions

Which of these would fit your schedule best?"""
        }
    ]
    
    # Process each turn in the conversation
    for turn in conversation:
        # Route query through semantic router
        response = await semantic_router.route_query(
            user_id="test_user_1",
            query=turn["query"]
        )
        
        # Create test case for this turn
        test_case = ConversationalTestCase(
            turns=[
                LLMTestCase(
                    input=turn["query"],
                    actual_output=response["response"],
                    expected_output=turn["expected_output"],
                    context=base_context
                )
            ]
        )
        
        # Evaluate response quality
        result = deepeval_evaluate(test_cases=[test_case], metrics=[metrics])
        
        # Verify response addresses expected focus areas
        response_text = response["response"].lower()
        focus_areas_found = [
            focus for focus in turn["expected_focus"]
            if focus.lower() in response_text
        ]
        assert len(focus_areas_found) > 0, f"Response did not address expected focus areas: {turn['expected_focus']}"
        
        # Verify response quality meets threshold
        assert any(test_result.success for test_result in result.test_results), "Response quality check failed"
        
        # Save successful test case
        if any(test_result.success for test_result in result.test_results):
            await test_session.update_dataset_with_passing_result(test_case)
    
    # Verify observation contexts were created and maintained
    assert "test_user_1" in semantic_router.observation_contexts, "No observation contexts created for test user"
    assert len(semantic_router.observation_contexts["test_user_1"]) > 0, "No observation contexts found for test user"
    
    # Verify route history was updated
    assert len(semantic_router.route_history) > 0, "No route history entries found"
    assert "method" in semantic_router.route_history[-1], "Route history entry missing method"
    
    # Verify test cases were saved
    assert await test_session.verify_saved_test_cases(), "Failed to save test cases to dataset"

def format_coach_response(response: Dict[str, Any]) -> str:
    """Format the coach's response into a standardized string format.
    
    Args:
        response: Raw response dictionary from the coach
        
    Returns:
        Formatted response string
    """
    if isinstance(response, str):
        return response
        
    formatted_parts = []
    
    # Add bio age assessment if present
    if "bio_age" in response:
        formatted_parts.append(f"Bio Age Assessment:\n{response['bio_age']}")
    
    # Add metrics if present
    if "metrics" in response:
        metrics = response["metrics"]
        formatted_parts.append("\nCurrent Metrics:")
        for metric, value in metrics.items():
            formatted_parts.append(f"• {metric}: {value}")
    
    # Add insights if present
    if "insights" in response:
        formatted_parts.append("\nInsights:")
        for insight in response["insights"]:
            formatted_parts.append(f"• {insight}")
    
    # Add recommendations if present
    if "recommendations" in response:
        formatted_parts.append("\nRecommendations:")
        for rec in response["recommendations"]:
            formatted_parts.append(f"• {rec}")
    
    # Add next steps if present
    if "next_steps" in response:
        formatted_parts.append("\nNext Steps:")
        for step in response["next_steps"]:
            formatted_parts.append(f"• {step}")
    
    return "\n".join(formatted_parts) 