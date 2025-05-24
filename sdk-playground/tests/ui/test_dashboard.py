import unittest
from unittest.mock import MagicMock, patch
import streamlit as st
from typing import List, Dict
from deepeval.test_case import ConversationalTestCase, LLMTestCase
from deepeval.dataset import EvaluationDataset

from src.data.dataset_generator import DatasetGenerator
from src.ui.dashboard import Dashboard
from src.models.conversation import Turn, ConversationMetrics, Conversation
from src.models.context import EvaluationContext

class TestDashboard(unittest.TestCase):
    def setUp(self):
        """Set up test environment before each test"""
        # Create a dict-like object that supports both attribute and item access
        class SessionState(dict):
            def __getattr__(self, key):
                return self[key]
            def __setattr__(self, key, value):
                self[key] = value
        
        # Mock streamlit session state
        self.mock_session_state = SessionState()
        self.patcher = patch('streamlit.session_state', self.mock_session_state)
        self.patcher.start()
        
        # Create sample data
        self.generator = DatasetGenerator()
        self.datasets = self.generator.generate_multiple_datasets([
            {"name": "Dataset 1", "num_conversations": 3}
        ])
        
        # Convert test cases to our internal model
        self.sample_conversations = []
        for test_case in self.datasets[0].test_cases:
            # Create two turns for each conversation
            turns = []
            for i in range(2):  # Ensure at least 2 turns
                turns.append(Turn(
                    id=f"turn_{i}",
                    coach_message=f"Coach message {i}",
                    user_message=f"User message {i}",
                    belief_updates={
                        "old": {},
                        "new": {}
                    },
                    timestamp=0.0
                ))
            
            context = EvaluationContext(
                user_cohort="test_cohort",
                router_intent="Lower BioAge Score",
                belief_system={},
                demographic_data={},
                session_history=[],
                learning_objectives=["test_objective"],
                confidence_scores={}
            )
            
            metrics = ConversationMetrics(
                user_identification=0.8,
                belief_evidencing=0.7,
                belief_verification=0.9,
                ambiguity=0.6,
                learning_progress=0.8,
                answer_prediction=0.7,
                question_clarity=0.8
            )
            
            conversation = Conversation(
                id=f"conv_{len(self.sample_conversations)}",
                turns=turns,
                context=context,
                metrics=metrics
            )
            self.sample_conversations.append(conversation)
        
        # Initialize dashboard
        self.dashboard = Dashboard()
        
    def tearDown(self):
        """Clean up after each test"""
        self.patcher.stop()
        
    def test_dashboard_initialization(self):
        """Test dashboard initialization"""
        # Verify session state initialization
        self.assertIn('current_turn_id', self.mock_session_state)
        self.assertIn('current_dataset', self.mock_session_state)
        self.assertIn('evaluation_status', self.mock_session_state)
        
    def test_handle_turn_selection(self):
        """Test turn selection updates session state"""
        # Set initial turn ID
        initial_turn_id = self.sample_conversations[0].turns[0].id
        self.mock_session_state['current_turn_id'] = initial_turn_id
        
        # Select new turn
        new_turn_id = self.sample_conversations[0].turns[1].id
        self.dashboard.handle_turn_selection(new_turn_id)
        
        # Verify turn ID was updated
        self.assertEqual(self.mock_session_state['current_turn_id'], new_turn_id)
        
    def test_render_main_view_updates_with_turn(self):
        """Test main view updates when turn changes"""
        # Set up turn and conversation
        conversation = self.sample_conversations[0]
        current_turn = conversation.turns[0]
        
        # Mock streamlit components
        with patch('streamlit.header') as mock_header, \
             patch('streamlit.write') as mock_write, \
             patch('streamlit.columns') as mock_columns:
            mock_columns.return_value = [MagicMock(), MagicMock()]
            
            # Render main view
            self.dashboard.render_main_view(conversation, current_turn)
            
            # Verify learning objective and messages were displayed
            mock_header.assert_called_with("Learning Objective")
            mock_write.assert_any_call(conversation.context.learning_objectives[0])
            mock_write.assert_any_call(current_turn.coach_message)
            mock_write.assert_any_call(current_turn.user_message)
            
    def test_render_with_empty_conversation(self):
        """Test dashboard handles empty conversation gracefully"""
        # Mock streamlit warning
        with patch('streamlit.warning') as mock_warning:
            # Render dashboard with empty conversation
            self.dashboard.render(
                conversation=None,
                available_datasets=['Dataset 1', 'Dataset 2', 'Dataset 3']
            )
            
            # Verify warning was shown
            mock_warning.assert_called_once()
            
    def test_render_with_invalid_turn_id(self):
        """Test dashboard handles invalid turn ID by selecting first turn"""
        # Set up invalid turn ID
        self.mock_session_state['current_turn_id'] = 'invalid_id'
        
        # Mock streamlit components to prevent actual rendering
        with patch('streamlit.columns') as mock_columns, \
             patch('streamlit.tabs') as mock_tabs:
            mock_columns.return_value = [MagicMock(), MagicMock()]
            mock_tabs.return_value = [MagicMock(), MagicMock()]
            
            # Render dashboard
            self.dashboard.render(
                conversation=self.sample_conversations[0],
                available_datasets=['Dataset 1', 'Dataset 2', 'Dataset 3']
            )
            
            # Verify turn ID was updated to first turn
            self.assertEqual(
                self.mock_session_state['current_turn_id'],
                self.sample_conversations[0].turns[0].id
            )

if __name__ == '__main__':
    unittest.main() 