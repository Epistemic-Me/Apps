from typing import Dict, List, Optional
from pydantic import BaseModel
from datetime import datetime

class BeliefSystem(BaseModel):
    """Represents a belief system for either Coach or User."""
    beliefs: Dict[str, float]  # belief_statement: confidence_score
    last_updated: datetime
    entropy: float

class SelfModel(BaseModel):
    """Represents the self-model of either Coach or User."""
    belief_system: BeliefSystem
    learning_progress: float
    model_version: str

class DialogueInteraction(BaseModel):
    """Represents a single interaction in the dialectic process."""
    id: str
    timestamp: datetime
    coach_message: str
    user_message: Optional[str]
    evaluation_score: Optional[float]
    belief_updates: Dict[str, float]  # Changes in belief confidence

class TrainingMetrics(BaseModel):
    """Tracks the training progress and metrics."""
    interaction_id: str
    entropy: float
    learning_progress: float
    timestamp: datetime

class EvaluationResult(BaseModel):
    """Represents the evaluation of an interaction."""
    interaction_id: str
    metrics: Dict[str, float]
    timestamp: datetime
    confidence_score: float 