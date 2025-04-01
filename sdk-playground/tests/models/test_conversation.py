import unittest
from datetime import datetime
from src.models.conversation import Conversation, Turn, ConversationMetrics
from src.models.context import EvaluationContext

class TestConversation(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.context = EvaluationContext(
            user_cohort="test_cohort",
            router_intent="test_intent",
            belief_system=["test_belief"],
            demographic_data=["test_demographic"],
            session_history=["test_session"],
            learning_objectives=["test_objective"],
            confidence_scores={"test_score": 0.9}
        )
        
        self.metrics = ConversationMetrics(
            user_identification=0.8,
            belief_evidencing=0.7,
            belief_verification=0.6,
            ambiguity=0.2,
            learning_progress=0.5,
            answer_prediction=0.4,
            question_clarity=0.9
        )
        
        self.conversation = Conversation(
            id="test_id",
            turns=[],
            metrics=self.metrics,
            context=self.context
        )

    def test_metrics_update(self):
        """Test updating conversation metrics from a dictionary"""
        update_dict = {
            "User Identification": 0.9,
            "Belief Evidencing": 0.8,
            "Question Clarity": 0.7
        }
        
        self.metrics.update(update_dict)
        
        self.assertEqual(self.metrics.user_identification, 0.9)
        self.assertEqual(self.metrics.belief_evidencing, 0.8)
        self.assertEqual(self.metrics.question_clarity, 0.7)
        # Other metrics should remain unchanged
        self.assertEqual(self.metrics.belief_verification, 0.6)

    def test_add_turn(self):
        """Test adding a new turn to the conversation"""
        coach_message = "How can I help you today?"
        user_message = "I want to improve my health."
        belief_updates = {
            "old": {"health_important": 0.5},
            "new": {"health_important": 0.7}
        }
        
        # Add turn and verify
        turn = self.conversation.add_turn(coach_message, user_message, belief_updates)
        
        self.assertEqual(len(self.conversation.turns), 1)
        self.assertEqual(turn.id, "0")
        self.assertEqual(turn.coach_message, coach_message)
        self.assertEqual(turn.user_message, user_message)
        self.assertEqual(turn.belief_updates, belief_updates)
        self.assertIsInstance(turn.timestamp, float)
        
        # Add another turn and verify ID increments
        turn2 = self.conversation.add_turn("Follow up?", "Yes", belief_updates)
        self.assertEqual(turn2.id, "1")

    def test_metrics_to_dict(self):
        """Test converting metrics to a dictionary"""
        metrics_dict = self.metrics.to_dict()
        
        self.assertEqual(metrics_dict["User Identification"], 0.8)
        self.assertEqual(metrics_dict["Belief Evidencing"], 0.7)
        self.assertEqual(metrics_dict["Belief Verification"], 0.6)
        self.assertEqual(metrics_dict["Ambiguity"], 0.2)
        self.assertEqual(metrics_dict["Learning Progress"], 0.5)
        self.assertEqual(metrics_dict["Answer Prediction"], 0.4)
        self.assertEqual(metrics_dict["Question Clarity"], 0.9)

if __name__ == '__main__':
    unittest.main() 