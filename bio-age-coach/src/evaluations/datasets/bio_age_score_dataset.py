"""
Dataset generator for BioAgeScore agent evaluations.

This module uses DeepEval's synthetic data generation to create realistic test cases
for the BioAgeScore agent, including user health data and conversations.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
from pathlib import Path
from deepeval.test_case import LLMTestCase, ConversationalTestCase, LLMTestCaseParams
from deepeval.dataset import EvaluationDataset
from deepeval import assert_test
from deepeval.metrics import ConversationalGEval
from deepeval.synthesizer import Synthesizer
from deepeval.synthesizer.config import StylingConfig

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define user profiles for context generation
USER_PROFILES = [
    {
        "age": 35,
        "gender": "male",
        "fitness_level": "intermediate",
        "health_goals": ["improve sleep", "increase activity", "reduce stress"],
        "current_habits": {
            "sleep_hours": 6.5,
            "active_calories": 300,
            "steps": 7000,
            "exercise_frequency": "2-3 times per week"
        },
        "health_beliefs": [
            "Sleep is important but work comes first",
            "Exercise is necessary but finding time is hard",
            "Stress management should be a priority"
        ]
    },
    {
        "age": 45,
        "gender": "female",
        "fitness_level": "beginner",
        "health_goals": ["weight management", "better sleep quality", "more energy"],
        "current_habits": {
            "sleep_hours": 7.0,
            "active_calories": 200,
            "steps": 5000,
            "exercise_frequency": "1-2 times per week"
        },
        "health_beliefs": [
            "It's harder to stay fit as you age",
            "Good sleep is essential for health",
            "Small changes can make a big difference"
        ]
    }
]

# Define conversation templates
CONVERSATION_TEMPLATES = [
    {
        "initial_query": "What's my current bio age score?",
        "expected_analysis": [
            "Calculate and explain bio age score",
            "Reference specific health metrics",
            "Compare to chronological age",
            "Identify areas for improvement"
        ]
    },
    {
        "initial_query": "How can I improve my biological age?",
        "expected_analysis": [
            "Review current health metrics",
            "Identify key areas for improvement",
            "Provide specific, actionable recommendations",
            "Set realistic goals"
        ]
    }
]

class BioAgeScoreDatasetGenerator:
    """Generator for bio age score test cases."""
    
    def __init__(self, api_key: str):
        """Initialize the dataset generator.
        
        Args:
            api_key: OpenAI API key
        """
        self.api_key = api_key
        # Create styling config for bio age coach test cases
        styling_config = StylingConfig(
            input_format="Questions about biological age, health metrics, and lifestyle recommendations",
            expected_output_format="Detailed responses that include bio age assessment, metrics analysis, and actionable recommendations",
            task="Providing personalized biological age coaching based on user health data",
            scenario="Users seeking to understand and improve their biological age through lifestyle changes"
        )
        self.synthesizer = Synthesizer(styling_config=styling_config)
        self.dataset_path = Path(__file__).parent / "bio_age_score_dataset.json"
    
    def generate_health_data(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Generate realistic health data based on user profile.
        
        Args:
            profile: User profile dictionary
            
        Returns:
            Dictionary of health metrics
        """
        habits = profile["current_habits"]
        # Add some random variation to make data more realistic
        return {
            "sleep_hours": habits["sleep_hours"] + (datetime.now().microsecond % 3 - 1) * 0.5,
            "active_calories": habits["active_calories"] + (datetime.now().microsecond % 100 - 50),
            "steps": habits["steps"] + (datetime.now().microsecond % 2000 - 1000),
            "date": datetime.now().strftime("%Y-%m-%d")
        }
    
    def create_test_cases(self) -> List[ConversationalTestCase]:
        """Create test cases from user profiles and conversation templates.
        
        Returns:
            List of ConversationalTestCase objects
        """
        test_cases = []
        for profile in USER_PROFILES:
            health_data = self.generate_health_data(profile)
            for template in CONVERSATION_TEMPLATES:
                # Create context strings
                context_strings = [
                    f"User Profile: {json.dumps(profile, indent=2)}",
                    f"Health Data: {json.dumps(health_data, indent=2)}",
                    f"Initial Query: {template['initial_query']}",
                    "Expected Analysis Points:",
                    *[f"- {point}" for point in template["expected_analysis"]]
                ]
                
                # Generate expected output based on health data and profile
                expected_output = self.generate_expected_output(health_data, profile, template)
                
                # Create LLMTestCase for the turn
                turn = LLMTestCase(
                    input=template["initial_query"],
                    actual_output=None,  # This will be filled by the agent during testing
                    expected_output=expected_output,
                    context=context_strings
                )
                
                # Create ConversationalTestCase with the turn
                test_case = ConversationalTestCase(turns=[turn])
                test_cases.append(test_case)
        
        return test_cases
    
    def generate_expected_output(self, health_data: Dict[str, Any], profile: Dict[str, Any], template: Dict[str, Any]) -> str:
        """Generate expected output based on health data and user profile.
        
        Args:
            health_data: Dictionary of health metrics
            profile: User profile dictionary
            template: Conversation template
            
        Returns:
            Expected output string
        """
        # Calculate bio age score based on health metrics
        bio_age_score = 0
        
        # Add years based on sleep deficit/surplus
        sleep_impact = (health_data["sleep_hours"] - 7.5) * -0.5  # Optimal sleep is 7.5 hours
        bio_age_score += sleep_impact
        
        # Add years based on activity level
        if health_data["active_calories"] < 300:
            bio_age_score += 2
        elif health_data["active_calories"] < 500:
            bio_age_score += 1
        
        if health_data["steps"] < 5000:
            bio_age_score += 2
        elif health_data["steps"] < 7500:
            bio_age_score += 1
        
        # Calculate final bio age
        chronological_age = profile["age"]
        biological_age = chronological_age + bio_age_score
        
        # Generate response based on template
        if template["initial_query"] == "What's my current bio age score?":
            return f"""Based on your health data, your biological age is {biological_age:.1f} years, which is {abs(bio_age_score):.1f} years {'higher' if bio_age_score > 0 else 'lower'} than your chronological age of {chronological_age}.

Key factors affecting your score:
- Sleep: You're getting {health_data['sleep_hours']} hours of sleep, which is {'below' if health_data['sleep_hours'] < 7.5 else 'above'} the optimal 7.5 hours
- Activity: You're burning {health_data['active_calories']} active calories and taking {health_data['steps']} steps per day
- Exercise frequency: {profile['current_habits']['exercise_frequency']}

To improve your biological age score, consider:
1. {'Increasing' if health_data['sleep_hours'] < 7.5 else 'Maintaining'} your sleep duration
2. {'Increasing' if health_data['active_calories'] < 500 else 'Maintaining'} your daily activity level
3. {'Increasing' if health_data['steps'] < 7500 else 'Maintaining'} your daily step count"""
        else:
            recommendations = []
            if health_data["sleep_hours"] < 7.5:
                recommendations.append(f"Aim to increase your sleep from {health_data['sleep_hours']} to 7.5-8 hours per night")
            if health_data["active_calories"] < 500:
                recommendations.append(f"Work towards burning 500+ active calories daily (currently at {health_data['active_calories']})")
            if health_data["steps"] < 7500:
                recommendations.append(f"Increase your daily steps from {health_data['steps']} to at least 7,500")
            
            return f"""Here are specific recommendations to improve your biological age score:

1. {recommendations[0] if recommendations else 'Maintain your current sleep habits'}
2. {recommendations[1] if len(recommendations) > 1 else 'Maintain your current activity level'}
3. {recommendations[2] if len(recommendations) > 2 else 'Maintain your current step count'}

Focus on these areas to reduce your biological age and improve your overall health. Remember to:
- Make gradual changes to build sustainable habits
- Track your progress daily
- Adjust your goals based on how you feel"""
    
    async def update_dataset_with_passing_result(self, test_case: ConversationalTestCase) -> None:
        """Update dataset with a passing test case result.
        
        Args:
            test_case: The passing test case to add to the dataset
        """
        try:
            # Load existing dataset
            test_cases_data = []
            if os.path.exists(self.dataset_path):
                with open(self.dataset_path, "r") as f:
                    test_cases_data = json.load(f)
            
            # Convert test case to dict format
            new_test_case_data = {
                "input": test_case.turns[0].input,
                "actual_output": test_case.turns[0].actual_output,
                "expected_output": test_case.turns[0].expected_output,
                "context": test_case.turns[0].context,
                "passed_at": datetime.now().isoformat(),
                "metrics_score": test_case.turns[0].metrics_score if hasattr(test_case.turns[0], 'metrics_score') else None
            }
            
            # Check if this test case already exists
            exists = False
            for i, tc in enumerate(test_cases_data):
                if tc["input"] == new_test_case_data["input"] and tc["context"] == new_test_case_data["context"]:
                    # Update existing test case with new results
                    test_cases_data[i] = new_test_case_data
                    exists = True
                    logger.info(f"Updated existing test case: {new_test_case_data['input']}")
                    break
            
            # Add new test case if it doesn't exist
            if not exists:
                test_cases_data.append(new_test_case_data)
                logger.info(f"Added new test case: {new_test_case_data['input']}")
            
            # Save updated dataset
            with open(self.dataset_path, "w") as f:
                json.dump(test_cases_data, f, indent=2)
            
            # Verify the save was successful by reading back the file
            with open(self.dataset_path, "r") as f:
                saved_data = json.load(f)
                if len(saved_data) != len(test_cases_data):
                    raise ValueError("Dataset verification failed: saved data length mismatch")
                
            logger.info(f"Successfully saved dataset with {len(test_cases_data)} test cases")
            
        except Exception as e:
            logger.error(f"Error updating dataset with passing result: {str(e)}")
            raise  # Re-raise the exception to ensure the caller knows about the failure

    async def synthesize_new_test_case(self, context: Dict[str, Any]) -> Optional[ConversationalTestCase]:
        """Synthesize a new test case based on the given context.
        
        Args:
            context: The context to use for synthesis, including user profile and health data
            
        Returns:
            A new ConversationalTestCase if successful, None otherwise
        """
        try:
            # Create a single context string with all information
            context_str = (
                f"User Profile:\n{json.dumps(context.get('user_profile', {}), indent=2)}\n\n"
                f"Health Data:\n{json.dumps(context.get('health_data', {}), indent=2)}"
            )
            
            # Generate new test case using synthesizer
            goldens = self.synthesizer.generate_goldens_from_contexts(
                contexts=[[context_str]],  # Double list to ensure proper format
                max_goldens_per_context=1
            )
            
            if goldens:
                golden = goldens[0]
                # Create LLMTestCase for the turn
                turn = LLMTestCase(
                    input=golden.input,
                    actual_output=None,
                    expected_output=golden.expected_output,
                    context=[context_str]  # Ensure context is a list
                )
                
                # Create ConversationalTestCase with the turn
                test_case = ConversationalTestCase(turns=[turn])
                logger.info(f"Successfully synthesized new test case")
                return test_case
            else:
                logger.error("Failed to synthesize test case: No test cases generated")
                return None
                
        except Exception as e:
            logger.error(f"Error synthesizing new test case: {str(e)}")
            return None

    async def generate_dataset(self) -> EvaluationDataset:
        """Generate evaluation dataset.
        
        Returns:
            Dataset object containing test cases
        """
        # Create test cases from templates
        test_cases = self.create_test_cases()
        
        # Create dataset
        dataset = EvaluationDataset(test_cases=test_cases)
        
        # Save test cases
        test_cases_data = [
            {
                "input": tc.turns[0].input,
                "actual_output": tc.turns[0].actual_output,
                "expected_output": tc.turns[0].expected_output,
                "context": tc.turns[0].context,
                "created_at": datetime.now().isoformat()
            }
            for tc in test_cases
        ]
        
        # Save dataset
        with open(self.dataset_path, "w") as f:
            json.dump(test_cases_data, f, indent=2)
        
        return dataset
    
    def load_dataset(self) -> EvaluationDataset:
        """Load existing dataset from file.
        
        Returns:
            Dataset object containing test cases
            
        Raises:
            FileNotFoundError: If dataset file doesn't exist
        """
        if not os.path.exists(self.dataset_path):
            raise FileNotFoundError(f"Dataset file not found at {self.dataset_path}")
        
        # Load test cases from file
        with open(self.dataset_path, "r") as f:
            test_cases_data = json.load(f)
        
        # Convert loaded data back to test cases
        test_cases = []
        for tc_data in test_cases_data:
            # Create LLMTestCase for the turn
            turn = LLMTestCase(
                input=tc_data["input"],
                actual_output=None,  # This will be filled by the agent during testing
                expected_output=tc_data["expected_output"],
                context=tc_data["context"]
            )
            
            # Create ConversationalTestCase with the turn
            test_case = ConversationalTestCase(turns=[turn])
            test_cases.append(test_case)
        
        return EvaluationDataset(test_cases=test_cases)

async def generate_bio_age_score_dataset(api_key: str) -> EvaluationDataset:
    """Generate BioAgeScore evaluation dataset.
    
    Args:
        api_key: OpenAI API key
        
    Returns:
        Generated dataset
    """
    generator = BioAgeScoreDatasetGenerator(api_key)
    return await generator.generate_dataset() 