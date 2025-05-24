from dataclasses import dataclass
from typing import Dict, List, Any

@dataclass
class EvaluationContext:
    user_cohort: str
    router_intent: str
    belief_system: Dict[str, float]
    demographic_data: Dict[str, Any]
    session_history: List[Dict]
    learning_objectives: List[str]
    confidence_scores: Dict[str, float]
    
    def to_dict(self) -> Dict:
        """Convert context to dictionary for DeepEval"""
        return {
            "user_cohort": self.user_cohort,
            "router_intent": self.router_intent,
            "belief_system": self.belief_system,
            "demographic_data": self.demographic_data,
            "session_history": self.session_history,
            "learning_objectives": self.learning_objectives,
            "confidence_scores": self.confidence_scores
        } 