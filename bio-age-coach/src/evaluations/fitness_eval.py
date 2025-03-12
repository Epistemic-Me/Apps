"""
Fitness metrics evaluation suite.
"""

from typing import List, Dict, Any
from deepeval.test_case import ConversationalTestCase, LLMTestCaseParams, LLMTestCase
from deepeval import evaluate
from evaluations.framework import EvaluationSuite, RouterContext
from bio_age_coach.types import DataCategory
import os
import asyncio
from bio_age_coach.mcp.tools_server import ToolsServer
from bio_age_coach.mcp.health_server import HealthServer

# Configure Confident AI tracking
os.environ["DEEPEVAL_API_KEY"] = os.getenv("CONFIDENT_AI_API_KEY", "")
os.environ["DEEPEVAL_DATASET_NAME"] = "fitness_metrics_evaluation"
os.environ["DEEPEVAL_EXPERIMENT_NAME"] = "fitness_coach_responses"

class FitnessMetricsEvaluation(EvaluationSuite):
    """Evaluation suite for fitness metrics queries."""
    
    async def setup(self):
        """Setup test environment with comprehensive fitness metrics data."""
        # Initialize test data with expanded metrics
        test_data = {
            "health_data": {
                "demographics": {
                    "age": 35,
                    "sex": "male",
                    "height": 175,
                    "weight": 70
                },
                "activity": {
                    "steps_per_day": 8000,
                    "exercise_minutes": 30,
                    "active_minutes": 45,
                    "heart_rate_zones": {
                        "low": 60,
                        "moderate": 120,
                        "high": 150
                    }
                }
            },
            "capabilities": {
                "walking": True,
                "light_exercise": True,
                "jogging": True,
                "strength_training": True,
                "flexibility_work": True
            },
            "fitness_metrics": {
                "push_ups": 30,
                "grip_strength": 90,
                "vo2_max": 45,
                "resting_heart_rate": 65,
                "one_leg_stand": 45,
                "sit_and_reach": 15
            }
        }
        
        # Initialize servers based on context
        if self.context.tools_server:
            await self.context.tools_server.initialize_data(test_data)
            
        if self.context.health_server:
            await self.context.health_server.initialize_data(test_data)
        
        # Initialize coach after data setup
        await super().setup()
        
        # Update coach's user data with all metrics
        if self.coach:
            self.coach.user_data.update(test_data)
    
    def create_test_case(self, input: str, expected_output: str, context: List[str], retrieval_context: List[str]) -> ConversationalTestCase:
        """Helper method to create a conversational test case."""
        # Add demographic and clinical info to context
        enhanced_context = context + [
            "User Profile: 35-year-old individual with intermediate fitness level",
            "Evaluation Focus: Comprehensive bio-age assessment and improvement",
            "Coaching Goal: Help user understand and improve their biological age through fitness"
        ]
        
        # Create initial turn with conversation history - more coaching focused
        initial_turn = LLMTestCase(
            input="Can you help me understand how my fitness metrics affect my biological age?",
            actual_output="I'd be happy to help you understand how your fitness metrics influence your biological age. Your fitness level plays a crucial role in determining how well your body is aging. Let's look at your metrics together and identify areas where we can help you feel younger and more vibrant. What would you like to focus on first?",
            expected_output="Warm, engaging greeting that connects fitness to biological age and establishes coaching relationship",
            context=enhanced_context,
            retrieval_context=retrieval_context
        )
        
        # Create the main turn for evaluation
        main_turn = LLMTestCase(
            input=input,
            actual_output=None,  # Initialize as None, will be set during evaluation
            expected_output=expected_output,
            context=enhanced_context,
            retrieval_context=retrieval_context
        )
        
        return ConversationalTestCase(
            turns=[initial_turn, main_turn],
            chatbot_role="Bio Age Coach"
        )

    def create_test_cases(self) -> List[ConversationalTestCase]:
        """Create comprehensive fitness-specific test cases."""
        # Define common context for all test cases
        base_context = [
            "User Demographics: Age 35, Individual",
            "Biological Age Context: Fitness metrics strongly influence biological age",
            "Strength Metrics: Push-ups: 30 reps, Grip strength: 90kg",
            "Cardiovascular Metrics: VO2 max: 45 ml/kg/min, Resting heart rate: 65 bpm",
            "Balance & Flexibility: One-leg stand: 45 seconds, Sit and reach: 15cm",
            "Daily Activity: Steps: 8,000, Exercise minutes: 30, Active minutes: 45",
            "Clinical Guidelines: ACSM Guidelines for Exercise Testing and Prescription, 11th Edition",
            "Safety Considerations: No reported injuries or limitations",
            "Coaching Approach: Motivational, supportive, focused on biological age improvement"
        ]
        
        # Add clinical context for better medical accuracy
        clinical_context = [
            "Reference Ranges:",
            "- VO2 max: 35-40 ml/kg/min (average), >45 ml/kg/min (excellent) for age 35",
            "- Resting heart rate: 60-100 bpm (normal range)",
            "- Daily steps: 10,000 steps (recommended target)",
            "- Exercise: 150-300 minutes/week moderate intensity (WHO guidelines)",
            "Bio-Age Impact:",
            "- Higher VO2 max correlates with lower biological age",
            "- Regular strength training can reduce biological age by 2-3 years",
            "- Consistent flexibility work improves joint and cellular health"
        ]
        
        base_context.extend(clinical_context)
        
        test_cases = [
            self.create_test_case(
                input="How do my current fitness metrics affect my biological age?",
                expected_output=(
                    "Great question! Let's look at how your fitness metrics are influencing your biological age:\n\n"
                    "🌟 Positive Impact on Bio-Age:\n"
                    "1. Strength Profile (reducing bio-age by ~2 years):\n"
                    "   - Push-ups: 30 reps (shows excellent functional strength)\n"
                    "   - Grip strength: 90kg (indicates robust muscle health)\n"
                    "2. Cardiovascular Health (reducing bio-age by ~1.5 years):\n"
                    "   - VO2 max: 45 ml/kg/min (excellent oxygen utilization)\n"
                    "   - Resting heart rate: 65 bpm (shows good heart efficiency)\n\n"
                    "🎯 Areas to Rejuvenate:\n"
                    "1. Daily Movement:\n"
                    "   - Current: 8,000 steps (target: 10,000 for optimal aging)\n"
                    "   - Exercise: 30 minutes (increasing to 45-60 mins could reduce bio-age further)\n"
                    "2. Flexibility & Balance:\n"
                    "   - One-leg stand: 45 seconds (good for joint health)\n"
                    "   - Sit and reach: 15cm (improving this could enhance cellular health)\n\n"
                    "I'm excited to help you optimize these metrics! Would you like to create a personalized plan to reduce your biological age further?"
                ),
                context=base_context,
                retrieval_context=["Complete bio-age and fitness metrics available"]
            ),
            self.create_test_case(
                input="Can you create a personalized exercise plan to reduce my biological age?",
                expected_output=(
                    "I'll help you create a plan that's specifically designed to reduce your biological age. Based on your metrics, here's what I recommend:\n\n"
                    "🎯 Weekly Training Plan:\n"
                    "1. Longevity-Focused Cardio (3x/week):\n"
                    "   - Start: 5 min warm-up at 60 bpm\n"
                    "   - Main: 20 min alternating between 120 bpm and 150 bpm\n"
                    "   - Progress to: 30-45 min sessions\n"
                    "   - Why: Could reduce bio-age by 2-3 years\n\n"
                    "2. Age-Reversing Strength (2-3x/week):\n"
                    "   - Build on your 30 push-ups\n"
                    "   - Maintain 90kg grip strength\n"
                    "   - Add compound movements\n"
                    "   - Why: Could reduce bio-age by 1-2 years\n\n"
                    "3. Cellular Health Sessions (2x/week):\n"
                    "   - Flexibility work to improve 15cm reach\n"
                    "   - Balance training to maintain 45s stand\n"
                    "   - Why: Enhances joint and cellular health\n\n"
                    "Let's start with this plan and adjust based on your progress. Which aspect would you like me to explain in more detail?"
                ),
                context=base_context,
                retrieval_context=["Exercise planning capabilities"]
            ),
            self.create_test_case(
                input="Calculate my potential biological age improvement based on my metrics",
                expected_output=(
                    "I'll use our bio-age calculation tools to analyze your potential improvement. Let me check that for you...\n\n"
                    "📊 Current Bio-Age Impact:\n"
                    "1. Cardiovascular Status: -1.5 years from chronological age\n"
                    "   - VO2 max at 45 ml/kg/min (excellent)\n"
                    "   - Resting HR at 65 bpm (optimal)\n\n"
                    "2. Strength Metrics: -2.0 years\n"
                    "   - Push-ups and grip strength above average\n\n"
                    "3. Activity Level: +0.5 years\n"
                    "   - Steps and exercise duration need improvement\n\n"
                    "🎯 Potential Improvement:\n"
                    "- Could reduce bio-age by additional 2-3 years by optimizing all metrics\n"
                    "- Primary focus areas: daily steps and exercise duration\n\n"
                    "Would you like me to create a targeted plan to achieve this improvement?"
                ),
                context=base_context,
                retrieval_context=["Bio-age calculation tools available"]
            ),
            self.create_test_case(
                input="What lifestyle changes will have the biggest impact on my biological age?",
                expected_output=(
                    "Based on your current metrics, here are the most impactful changes for reducing your biological age:\n\n"
                    "🌟 High-Impact Changes:\n"
                    "1. Optimize Daily Movement (potential 2-year reduction):\n"
                    "   - Increase steps from 8,000 to 10,000\n"
                    "   - Boost exercise from 30 to 45-60 mins\n"
                    "   - Why: Enhances cellular repair and longevity\n\n"
                    "2. Maintain Strength (current 2-year reduction):\n"
                    "   - Keep excellent grip strength (90kg)\n"
                    "   - Continue push-up capacity (30 reps)\n"
                    "   - Why: Preserves muscle mass and metabolic health\n\n"
                    "3. Enhance Recovery (potential 1-year reduction):\n"
                    "   - Improve flexibility (currently 15cm)\n"
                    "   - Maintain balance (45s stand)\n"
                    "   - Monitor heart rate (65 bpm is great)\n\n"
                    "Would you like to create a weekly schedule to implement these changes gradually?"
                ),
                context=base_context,
                retrieval_context=["Lifestyle impact analysis"]
            ),
            self.create_test_case(
                input="Can you analyze my metrics and calculate a personalized longevity score?",
                expected_output=(
                    "I'll use our bio-age analysis tools to calculate your longevity score and provide personalized insights.\n\n"
                    "[Tool Usage: Calculating longevity score using health metrics...]\n\n"
                    "📊 Longevity Analysis Results:\n"
                    "1. Current Biological Age: 33.5 years (1.5 years younger than chronological)\n"
                    "2. Longevity Score: 85/100\n"
                    "   - Cardiovascular health: 90/100\n"
                    "   - Strength metrics: 88/100\n"
                    "   - Mobility & flexibility: 75/100\n\n"
                    "[Tool Usage: Generating personalized recommendations...]\n\n"
                    "🎯 Personalized Action Items:\n"
                    "1. Cardiovascular Optimization:\n"
                    "   - Maintain excellent VO2 max of 45 ml/kg/min\n"
                    "   - Add 2 HIIT sessions per week\n"
                    "2. Strength Enhancement:\n"
                    "   - Progressive overload for grip strength\n"
                    "   - Add lower body compound exercises\n"
                    "3. Mobility Improvement:\n"
                    "   - Daily flexibility routine\n"
                    "   - Focus on hip and shoulder mobility\n\n"
                    "Would you like me to create a detailed weekly plan targeting these areas?"
                ),
                context=base_context + [
                    "Tool Integration: Bio-age calculation and recommendation tools available",
                    "Expected Tool Chain: Health metrics → Bio-age calculation → Personalized recommendations"
                ],
                retrieval_context=["Bio-age tools and recommendation engine"]
            )
        ]
        return test_cases

async def main():
    """Run the fitness metrics evaluation suite."""
    # Initialize servers
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")
    
    try:
        # Create and initialize servers
        tools_server = ToolsServer(api_key)
        health_server = HealthServer(api_key)
        
        # Create context with initialized servers
        context = RouterContext(
            tools_server=tools_server,
            health_server=health_server
        )
        
        # Create and run evaluation
        evaluation = FitnessMetricsEvaluation(context)
        await evaluation.setup()  # Initialize test data
        results = await evaluation.run_evaluation()
        
        print("\nFitness Metrics Evaluation Results:")
        print("=" * 50)
        
        # Process all test cases first
        processed_test_cases = []
        for result in results:
            if result and isinstance(result, ConversationalTestCase):
                last_turn = result.turns[-1]
                print(f"\nTest Case: {last_turn.input}")
                print(f"Expected Output: {last_turn.expected_output}")
                print(f"Actual Output: {last_turn.actual_output}")
                processed_test_cases.append(result)
            else:
                print("Test case failed to process")
        
        # Batch evaluate all test cases together
        if processed_test_cases:
            print("\nEvaluating all test cases as a batch:")
            evaluation_results = evaluate(
                test_cases=processed_test_cases,
                metrics=evaluation.metrics
            )
            
            # Let Confident AI handle the metric result printing
            print("\nSee full results in Confident AI dashboard")
                
    except Exception as e:
        print(f"Error running fitness evaluation: {e}")
        raise  # Re-raise the exception for better error tracking

if __name__ == "__main__":
    asyncio.run(main()) 