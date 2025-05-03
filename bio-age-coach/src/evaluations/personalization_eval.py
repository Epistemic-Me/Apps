"""
Personalization evaluation suite for testing the AI Coach's ability to understand and adapt to users.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import sqlite3
import os
import asyncio
from dataclasses import dataclass
from deepeval.test_case import ConversationalTestCase, LLMTestCase, LLMTestCaseParams
from deepeval.metrics import ConversationalGEval
from deepeval import evaluate
from evaluations.framework import EvaluationSuite, RouterContext
from bio_age_coach.agents.specialized.bio_age_score_agent import BioAgeScoreAgent
from bio_age_coach.mcp.client import MultiServerMCPClient

@dataclass
class UserProfile:
    """User profile for testing personalization."""
    user_id: str
    health_data_summary: Dict[str, Any]
    current_habits: List[Dict[str, Any]]
    target_habits: List[Dict[str, Any]]
    beliefs: Dict[str, Any]
    change_readiness: Dict[str, float]

class PersonalizationEvaluation(EvaluationSuite):
    """Evaluation suite for testing personalization in coaching sessions."""
    
    def _initialize_metrics(self):
        """Initialize evaluation metrics for personalization testing."""
        self.habit_understanding = ConversationalGEval(
            name="Habit Understanding",
            criteria="""Given the 'actual output' are generated responses from the Bio Age Coach
            and 'input' are user statements about their habits, determine whether the chatbot:
            1. Accurately identifies and reflects back current habits
            2. Shows understanding of habit formation and maintenance
            3. Makes connections between different habits
            4. Recognizes patterns in user behavior
            5. Acknowledges both positive and challenging aspects of habits""",
            evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.INPUT],
            threshold=0.7
        )
        
        self.belief_exploration = ConversationalGEval(
            name="Belief Exploration",
            criteria="""Given the 'actual output' are generated responses from the Bio Age Coach
            and 'input' are user statements about their health beliefs, determine whether the chatbot:
            1. Explores underlying beliefs about health and change
            2. Validates user's existing health beliefs
            3. Gently challenges limiting beliefs when appropriate
            4. Makes connections between beliefs and behaviors
            5. Uses belief exploration to guide recommendations""",
            evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.INPUT],
            threshold=0.7
        )
        
        self.change_readiness = ConversationalGEval(
            name="Change Readiness Assessment",
            criteria="""Given the 'actual output' are generated responses from the Bio Age Coach
            and 'input' are user statements about potential changes, determine whether the chatbot:
            1. Assesses readiness for specific changes
            2. Adapts recommendations based on readiness level
            3. Provides appropriate support for user's stage of change
            4. Recognizes barriers and facilitators to change
            5. Helps build confidence in ability to change""",
            evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.INPUT],
            threshold=0.7
        )
        
        self.recommendation_personalization = ConversationalGEval(
            name="Recommendation Personalization",
            criteria="""Given the 'actual output' are generated responses from the Bio Age Coach
            and 'expected output' are ideal responses, determine whether recommendations:
            1. Are tailored to user's current habits and lifestyle
            2. Consider user's beliefs and values
            3. Account for user's readiness to change
            4. Build on user's strengths and successes
            5. Address specific barriers mentioned by user""",
            evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.EXPECTED_OUTPUT],
            threshold=0.7
        )
    
    def _create_test_user_profile(self) -> UserProfile:
        """Create a test user profile with realistic data."""
        return UserProfile(
            user_id="test_user_1",
            health_data_summary={
                "sleep": {
                    "average_duration": 7.2,
                    "quality": "moderate",
                    "consistency": "variable"
                },
                "exercise": {
                    "weekly_active_days": 3,
                    "preferred_activities": ["walking", "yoga"],
                    "intensity_level": "moderate"
                },
                "nutrition": {
                    "meal_regularity": "good",
                    "diet_quality": "mixed",
                    "areas_for_improvement": ["protein intake", "vegetable variety"]
                }
            },
            current_habits=[
                {
                    "category": "sleep",
                    "habit": "irregular bedtime",
                    "frequency": "variable",
                    "triggers": ["work deadlines", "evening screen time"],
                    "barriers": ["stress", "inconsistent schedule"]
                },
                {
                    "category": "exercise",
                    "habit": "morning walks",
                    "frequency": "3x per week",
                    "triggers": ["morning routine", "weather"],
                    "facilitators": ["dog walking", "podcast listening"]
                }
            ],
            target_habits=[
                {
                    "category": "sleep",
                    "habit": "consistent 10pm bedtime",
                    "desired_frequency": "daily",
                    "implementation_intention": "After 9pm evening routine, head to bedroom"
                },
                {
                    "category": "exercise",
                    "habit": "strength training",
                    "desired_frequency": "3x per week",
                    "implementation_intention": "After morning walk, do 15-min strength routine"
                }
            ],
            beliefs={
                "sleep": [
                    "getting enough sleep helps manage stress",
                    "screen time affects sleep quality",
                    "consistent schedule is important but hard"
                ],
                "exercise": [
                    "any movement is better than none",
                    "morning exercise sets up the day well",
                    "strength training seems intimidating"
                ]
            },
            change_readiness={
                "sleep_schedule": 0.7,  # Preparation stage
                "strength_training": 0.3,  # Contemplation stage
                "nutrition_tracking": 0.5  # Preparation stage
            }
        )
    
    def _store_test_data(self, user_profile: UserProfile):
        """Store test data in SQLite database."""
        db_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "test.db")
        
        # Create database and tables if they don't exist
        conn = sqlite3.connect(db_path)
        with open(os.path.join(os.path.dirname(__file__), "..", "..", "data", "user_profile_schema.sql")) as f:
            conn.executescript(f.read())
        
        # Store user profile
        conn.execute("""
            INSERT OR REPLACE INTO user_profiles (
                user_id, health_data_summary, current_habits, target_habits, 
                beliefs, change_readiness
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            user_profile.user_id,
            json.dumps(user_profile.health_data_summary),
            json.dumps(user_profile.current_habits),
            json.dumps(user_profile.target_habits),
            json.dumps(user_profile.beliefs),
            json.dumps(user_profile.change_readiness)
        ))
        
        conn.commit()
        conn.close()
    
    async def setup(self) -> None:
        """Set up the test environment."""
        # Initialize metrics
        self._initialize_metrics()
        
        # Create and store test user profile
        user_profile = self._create_test_user_profile()
        self._store_test_data(user_profile)
        
        # Initialize bio age score server with test data
        bio_age_score_server = self.context.mcp_client.servers.get("bio_age_score")
        if not bio_age_score_server:
            raise ValueError("Bio age score server not found in MCP client")
        
        await bio_age_score_server.initialize_data({
            "user_id": user_profile.user_id,
            "health_data": user_profile.health_data_summary
        })
    
    def create_test_cases(self) -> List[ConversationalTestCase]:
        """Create test cases for personalization testing."""
        test_cases = []
        
        # Test Case 1: Habit Understanding
        habit_assessment_turns = [
            LLMTestCase(
                input="I try to go to bed at 10pm but often get caught up with work and end up staying up late.",
                actual_output=None,
                expected_output="""I hear that you're aiming for a 10pm bedtime, which is a great goal. It sounds like work demands are making this challenging.

Let's explore this a bit:
1. What typically happens on evenings when you do manage to stick to your 10pm bedtime?
2. Are there specific types of work tasks that tend to keep you up?
3. How does your morning feel different when you succeed vs when work keeps you up late?

Understanding these patterns will help us develop strategies that work with your schedule."""
            ),
            LLMTestCase(
                input="When I do stick to 10pm, I feel much better the next day. Usually it's emails and finishing up projects that keep me up.",
                actual_output=None,
                expected_output="""Thank you for sharing that insight! I'm noticing a clear connection between your bedtime and next-day wellbeing.

Based on what you've shared:
✓ You've experienced the benefits of a 10pm bedtime
✓ Work emails and project completion are your main sleep barriers
✓ You have evidence that this habit improves your daily functioning

Would you be interested in exploring some strategies for wrapping up work earlier, perhaps setting a "work boundary time" that still lets you handle important tasks but protects your sleep schedule?"""
            )
        ]
        
        test_cases.append(
            ConversationalTestCase(
                turns=habit_assessment_turns,
                chatbot_role="Bio Age Coach"
            )
        )
        
        # Test Case 2: Belief Exploration
        belief_exploration_turns = [
            LLMTestCase(
                input="I believe I need to do intense workouts to get any real benefit from exercise.",
                actual_output=None,
                expected_output="""I appreciate you sharing that belief about exercise intensity. Let's explore this together.

Research actually shows that different types of movement offer different benefits:
- Light activity (like walking) improves cardiovascular health and reduces stress
- Moderate exercise builds endurance and maintains muscle
- Intense workouts can boost fitness but aren't the only path to health

What makes you feel that intense workouts are necessary? Have you had experiences with different types of exercise?"""
            ),
            LLMTestCase(
                input="Well, I notice I feel more accomplished after an intense workout, but I struggle to maintain that routine.",
                actual_output=None,
                expected_output="""I hear two important things:
1. Intense workouts give you a sense of accomplishment
2. The intensity makes it challenging to maintain consistently

This helps me understand your perspective better. The feeling of accomplishment is valuable! But let's consider:
- How might you get that same feeling of accomplishment through a more sustainable routine?
- What if we could build a mixed approach that includes both intense and moderate activities?
- Would you be open to exploring how different types of movement could support your health goals?"""
            )
        ]
        
        test_cases.append(
            ConversationalTestCase(
                turns=belief_exploration_turns,
                chatbot_role="Bio Age Coach"
            )
        )
        
        # Test Case 3: Change Readiness Assessment
        change_readiness_turns = [
            LLMTestCase(
                input="I've been thinking about adding strength training but I'm not sure where to start.",
                actual_output=None,
                expected_output="""Thank you for sharing that interest in strength training. I notice you're thinking about it but feeling uncertain about the first steps.

Let's understand where you are with this:
1. What attracts you to strength training?
2. On a scale of 1-10, how confident do you feel about starting?
3. What would help you feel more prepared to begin?

This will help us create a plan that matches your comfort level and readiness."""
            ),
            LLMTestCase(
                input="I'd say my confidence is about 4/10. I know it's good for health but I'm worried about proper form and injury.",
                actual_output=None,
                expected_output="""I appreciate your honesty about your confidence level, and your concern about form and safety is very valid.

Given where you are now:
✓ You recognize the health benefits
✓ You're prioritizing safety and proper technique
✓ You're at a stage of careful consideration

Would you be interested in starting with:
1. Learning about basic movement patterns?
2. Watching technique demonstrations?
3. Starting with simple bodyweight exercises?

We can build your confidence gradually while ensuring safety."""
            )
        ]
        
        test_cases.append(
            ConversationalTestCase(
                turns=change_readiness_turns,
                chatbot_role="Bio Age Coach"
            )
        )
        
        return test_cases
    
    async def run_evaluation(self) -> List[ConversationalTestCase]:
        """Run the evaluation and return test cases with results."""
        # Set up the test environment
        await self.setup()
        
        # Create test cases
        test_cases = self.create_test_cases()
        
        # Process each test case
        for test_case in test_cases:
            for turn in test_case.turns:
                # Process the query with the agent
                response = await self.bio_age_score_agent.process(turn.input, self.context.context)
                
                # Set the actual output
                turn.actual_output = response.get("response", "")
        
        # Run evaluation
        results = evaluate(test_cases, metrics=self.metrics)
        
        return test_cases

async def main():
    """Run the evaluation."""
    # Create MCP client
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")
        
    mcp_client = MultiServerMCPClient(api_key=api_key)
    
    # Create router context
    context = RouterContext(mcp_client=mcp_client)
    
    # Create evaluation suite
    evaluation = PersonalizationEvaluation(context)
    
    # Run evaluation
    test_cases = await evaluation.run_evaluation()
    
    # Print results
    for i, test_case in enumerate(test_cases):
        print(f"\nTest Case {i+1}:")
        for j, turn in enumerate(test_case.turns):
            print(f"  Turn {j+1}:")
            print(f"    Input: {turn.input}")
            print(f"    Expected: {turn.expected_output}")
            print(f"    Actual: {turn.actual_output}")
            print(f"    Metrics: {turn.metrics}")

if __name__ == "__main__":
    asyncio.run(main()) 