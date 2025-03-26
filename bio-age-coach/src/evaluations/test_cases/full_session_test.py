"""
Test case for evaluating a full coaching session.
"""

from typing import List, Dict, Any
from dataclasses import dataclass
from deepeval.test_case import ConversationalTestCase, LLMTestCase
from bio_age_coach.agents.specialized.bio_age_score_agent import BioAgeScoreAgent
from evaluations.scoring import PersonalizationScoring

@dataclass
class SessionContext:
    """Context for a coaching session."""
    health_data: Dict[str, Any]
    current_habits: List[Dict[str, Any]]
    beliefs: Dict[str, Any]
    change_readiness: Dict[str, float]

class FullSessionTest:
    """Test case for a complete coaching session."""
    
    def __init__(self):
        self.scoring = PersonalizationScoring()
    
    def create_test_session(self) -> ConversationalTestCase:
        """Create a test case for a full coaching session."""
        
        # Initial context with health data and habits
        context = SessionContext(
            health_data={
                "bio_age_score": {
                    "overall_score": 85,
                    "sleep_score": 70,
                    "exercise_score": 90,
                    "movement_score": 95
                },
                "sleep": {
                    "average_duration": 6.8,
                    "deep_sleep_percentage": 20,
                    "sleep_efficiency": 85
                },
                "exercise": {
                    "active_days_per_week": 4,
                    "average_intensity": "moderate",
                    "preferred_activities": ["running", "yoga"]
                }
            },
            current_habits=[
                {
                    "category": "sleep",
                    "habit": "late bedtime",
                    "frequency": "5-6 nights/week",
                    "triggers": ["work stress", "evening screen time"],
                    "barriers": ["racing thoughts", "irregular schedule"]
                },
                {
                    "category": "exercise",
                    "habit": "morning run",
                    "frequency": "3x per week",
                    "triggers": ["morning routine", "running buddy"],
                    "facilitators": ["social support", "morning energy"]
                }
            ],
            beliefs={
                "sleep": [
                    "I can catch up on sleep on weekends",
                    "Screen time doesn't affect me much",
                    "I'm naturally a night person"
                ],
                "exercise": [
                    "Morning exercise gives me energy",
                    "I need variety to stay motivated",
                    "Social support helps me stay consistent"
                ]
            },
            change_readiness={
                "sleep_schedule": 0.6,  # Contemplation/Preparation
                "exercise_intensity": 0.8,  # Preparation/Action
                "stress_management": 0.4  # Contemplation
            }
        )
        
        # Create conversation turns for a full session
        turns = [
            # Turn 1: Initial Assessment
            LLMTestCase(
                input="Hi, I'd like to understand my bio-age score and how I can improve it.",
                actual_output=None,
                expected_output="""Welcome! I see your bio-age score is 85, which is good but has room for improvement. Let's look at your components:

✓ Movement score: 95 (Excellent)
✓ Exercise score: 90 (Very Good)
✓ Sleep score: 70 (Room for improvement)

I notice you're getting about 6.8 hours of sleep on average. How do you feel about your current sleep patterns?"""
            ),
            
            # Turn 2: Sleep Exploration
            LLMTestCase(
                input="I tend to go to bed late because of work and screen time. I try to catch up on weekends.",
                actual_output=None,
                expected_output="""I hear you about the late bedtime and catching up on weekends. Let me share something interesting:

Research shows that consistent sleep timing is actually more important than total hours - we can't really "catch up" on weekends. Your body's internal clock works best with regularity.

I notice:
✓ Work stress and screen time are key triggers
✓ You're experiencing racing thoughts at bedtime
✓ You identify as a "night person"

Where would you rate your readiness to work on sleep timing, on a scale of 1-10?"""
            ),
            
            # Turn 3: Belief Exploration
            LLMTestCase(
                input="Maybe a 6? I know I should change but it's hard with my schedule. I don't think screens affect me much though.",
                actual_output=None,
                expected_output="""Thank you for sharing that openness to change while being honest about the challenges. Let's explore the screen time belief:

• Have you ever tracked your sleep quality with vs without evening screen time?
• What makes you feel screens don't affect you much?

Your readiness score suggests you're considering changes but need them to work with your schedule. Would you be interested in experimenting with small adjustments to test these beliefs?"""
            ),
            
            # Turn 4: Habit Formation
            LLMTestCase(
                input="I could try. What kind of adjustments would work with my schedule?",
                actual_output=None,
                expected_output="""Great! Let's build on what's already working for you. I notice you successfully maintain a morning running routine with social support.

Given your schedule and current habits, here are some personalized suggestions:

1. Tiny First Step:
   • Set a "wind-down" alarm 30 minutes before your target bedtime
   • Just like your morning run has a trigger (running buddy), this alarm becomes your evening trigger

2. Work With Your Pattern:
   • Instead of a dramatic change, start with 15 minutes earlier than your usual bedtime
   • Use your "night person" energy for planning tomorrow, so morning feels easier

3. Social Support:
   • Since social support helps with your running, could you find an "accountability buddy" for evening routine?

Which of these resonates most with your situation?"""
            ),
            
            # Turn 5: Action Planning
            LLMTestCase(
                input="I like the wind-down alarm idea and starting with 15 minutes earlier. How do I handle work deadlines though?",
                actual_output=None,
                expected_output="""Excellent choice! Let's create a realistic plan that accounts for work demands:

1. Wind-Down Alarm Strategy:
   ✓ Set alarm for 10:45 PM (15 minutes earlier than usual)
   ✓ When it rings, finish current task (don't start new ones)
   ✓ Use next 30 minutes for tomorrow's planning

2. Deadline Management:
   • Identify "must-do-tonight" vs "can-wait" tasks at 5 PM
   • Set specific cut-off time for each task
   • Create a "parking lot" list for tomorrow

Would you like to try this for the next week and track how it affects your morning energy and bio-age score?"""
            )
        ]
        
        return ConversationalTestCase(
            turns=turns,
            chatbot_role="Bio Age Coach",
            metadata={
                "session_context": context,
                "evaluation_criteria": {
                    "habit_understanding": self.scoring.habit_criteria,
                    "belief_exploration": self.scoring.belief_criteria,
                    "change_readiness": self.scoring.readiness_criteria,
                    "recommendation_personalization": self.scoring.recommendation_criteria
                }
            }
        )
    
    def evaluate_session(self, test_case: ConversationalTestCase) -> Dict[str, float]:
        """Evaluate a full coaching session."""
        scores = {}
        
        for metric_name, criteria in test_case.metadata["evaluation_criteria"].items():
            metric = self.scoring.create_evaluation_metric(criteria)
            
            # Evaluate each turn
            turn_scores = []
            for turn in test_case.turns:
                if turn.actual_output:  # Skip if no actual output yet
                    score = metric.measure(turn.actual_output, turn.expected_output)
                    turn_scores.append(score)
                    
                    # Print detailed feedback
                    print(self.scoring.explain_score(
                        metric_name,
                        score,
                        turn.actual_output
                    ))
            
            # Average score for this metric
            scores[metric_name] = sum(turn_scores) / len(turn_scores) if turn_scores else 0.0
        
        return scores

async def run_full_session_test(agent: BioAgeScoreAgent) -> Dict[str, float]:
    """Run a full session test with the bio age score agent."""
    test = FullSessionTest()
    test_case = test.create_test_session()
    
    # Process each turn with the agent
    for turn in test_case.turns:
        response = await agent.process(
            turn.input,
            test_case.metadata["session_context"]
        )
        turn.actual_output = response.get("response", "")
    
    # Evaluate the session
    scores = test.evaluate_session(test_case)
    
    return scores 