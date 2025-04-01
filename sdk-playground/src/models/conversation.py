from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime

from .context import EvaluationContext

@dataclass
class Turn:
    id: str
    coach_message: str
    user_message: str
    belief_updates: Dict[str, Dict[str, float]]  # {old: {belief: score}, new: {belief: score}}
    timestamp: float
    metrics: Optional[Dict[str, float]] = None

@dataclass
class ConversationMetrics:
    user_identification: float
    belief_evidencing: float
    belief_verification: float
    ambiguity: float
    learning_progress: float
    answer_prediction: float
    question_clarity: float
    
    def to_dict(self) -> Dict[str, float]:
        return {
            "User Identification": self.user_identification,
            "Belief Evidencing": self.belief_evidencing,
            "Belief Verification": self.belief_verification,
            "Ambiguity": self.ambiguity,
            "Learning Progress": self.learning_progress,
            "Answer Prediction": self.answer_prediction,
            "Question Clarity": self.question_clarity
        }
    
    def update(self, metrics_dict: Dict[str, float]):
        """Update metrics from a dictionary"""
        for key, value in metrics_dict.items():
            if hasattr(self, key.lower().replace(" ", "_")):
                setattr(self, key.lower().replace(" ", "_"), value)

@dataclass
class Conversation:
    id: str
    turns: List[Turn]
    metrics: ConversationMetrics
    context: EvaluationContext
    
    def add_turn(self, coach_message: str, user_message: str, belief_updates: Dict[str, Dict[str, float]]):
        """Add a new turn to the conversation"""
        turn = Turn(
            id=str(len(self.turns)),
            coach_message=coach_message,
            user_message=user_message,
            belief_updates=belief_updates,
            timestamp=datetime.now().timestamp()
        )
        self.turns.append(turn)
        return turn 