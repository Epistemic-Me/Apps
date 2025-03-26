"""
Scoring module for personalization evaluation metrics.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import json
from deepeval.metrics import ConversationalGEval

@dataclass
class ScoringCriteria:
    """Criteria for scoring a specific aspect of personalization."""
    name: str
    weight: float
    indicators: List[str]
    examples: Dict[str, List[str]]

class PersonalizationScoring:
    """Scoring system for personalization metrics."""
    
    def __init__(self):
        self.habit_criteria = ScoringCriteria(
            name="Habit Understanding",
            weight=0.25,
            indicators=[
                "Reflects user's stated habits accurately",
                "Identifies habit triggers and barriers",
                "Makes connections between habits",
                "Recognizes habit patterns",
                "Acknowledges both successes and challenges"
            ],
            examples={
                "high_score": [
                    "I hear that you're aiming for a 10pm bedtime... work demands are making this challenging",
                    "You've noticed that morning walks help you start the day well, especially when combined with podcast listening"
                ],
                "low_score": [
                    "You should go to bed earlier",
                    "Try to exercise more"
                ]
            }
        )
        
        self.belief_criteria = ScoringCriteria(
            name="Belief Exploration",
            weight=0.25,
            indicators=[
                "Validates existing health beliefs",
                "Explores belief origins",
                "Connects beliefs to behaviors",
                "Gently challenges limiting beliefs",
                "Uses beliefs to guide recommendations"
            ],
            examples={
                "high_score": [
                    "I understand your belief about intense workouts... Let's explore what makes you feel that way",
                    "Your experience with morning exercise setting up your day aligns with research showing..."
                ],
                "low_score": [
                    "That belief is incorrect",
                    "You should change how you think about exercise"
                ]
            }
        )
        
        self.readiness_criteria = ScoringCriteria(
            name="Change Readiness",
            weight=0.25,
            indicators=[
                "Assesses current stage of change",
                "Adapts approach to readiness level",
                "Builds confidence appropriately",
                "Identifies readiness signals",
                "Provides stage-appropriate support"
            ],
            examples={
                "high_score": [
                    "I notice you're thinking about strength training but feeling uncertain. Let's explore what would help you feel more prepared",
                    "Given your confidence level of 4/10, let's start with some basic movements..."
                ],
                "low_score": [
                    "Here's a complete workout plan",
                    "Just start doing it tomorrow"
                ]
            }
        )
        
        self.recommendation_criteria = ScoringCriteria(
            name="Recommendation Personalization",
            weight=0.25,
            indicators=[
                "Tailors to current habits",
                "Considers stated beliefs",
                "Matches readiness level",
                "Builds on strengths",
                "Addresses specific barriers"
            ],
            examples={
                "high_score": [
                    "Since you already enjoy morning walks, we could add a 5-minute strength routine right after",
                    "Knowing your concern about form, let's start with these basic movements..."
                ],
                "low_score": [
                    "Here's a standard exercise plan",
                    "These are good habits for everyone"
                ]
            }
        )
    
    def create_evaluation_metric(self, criteria: ScoringCriteria) -> ConversationalGEval:
        """Create a ConversationalGEval metric from scoring criteria."""
        return ConversationalGEval(
            name=criteria.name,
            criteria=self._format_criteria(criteria),
            threshold=0.7
        )
    
    def _format_criteria(self, criteria: ScoringCriteria) -> str:
        """Format criteria for ConversationalGEval."""
        return f"""Given the 'actual output' are generated responses from the Bio Age Coach,
        evaluate whether the response demonstrates {criteria.name} by checking:
        
        Indicators (each worth {1/len(criteria.indicators):.2f} points):
        {self._format_indicators(criteria.indicators)}
        
        High-scoring examples:
        {self._format_examples(criteria.examples['high_score'])}
        
        Low-scoring examples:
        {self._format_examples(criteria.examples['low_score'])}
        """
    
    def _format_indicators(self, indicators: List[str]) -> str:
        """Format indicators as numbered list."""
        return "\n".join(f"{i+1}. {indicator}" for i, indicator in enumerate(indicators))
    
    def _format_examples(self, examples: List[str]) -> str:
        """Format examples as bullet points."""
        return "\n".join(f"• {example}" for example in examples)
    
    def explain_score(self, metric_name: str, score: float, response: str) -> str:
        """Explain why a response received a particular score."""
        criteria = getattr(self, f"{metric_name.lower()}_criteria")
        
        explanation = [
            f"Score for {criteria.name}: {score:.2f}",
            "\nStrengths:",
        ]
        
        # Add matched indicators
        for indicator in criteria.indicators:
            if any(example.lower() in response.lower() for example in criteria.examples["high_score"]):
                explanation.append(f"✓ {indicator}")
        
        explanation.extend([
            "\nAreas for Improvement:",
            "Consider incorporating more:"
        ])
        
        # Add missing indicators
        for indicator in criteria.indicators:
            if not any(example.lower() in response.lower() for example in criteria.examples["high_score"]):
                explanation.append(f"• {indicator}")
        
        return "\n".join(explanation)

def get_scoring_system() -> PersonalizationScoring:
    """Get the personalization scoring system."""
    return PersonalizationScoring() 