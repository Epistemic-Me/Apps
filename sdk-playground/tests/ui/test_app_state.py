import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import streamlit as st
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.ui.components.conversation_selector import ConversationSelector
from src.data.dataset_generator import DatasetGenerator
from deepeval.dataset import EvaluationDataset

class TestAppState(unittest.TestCase):
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
        
        # Create sample datasets
        self.generator = DatasetGenerator()
        self.datasets = self.generator.generate_multiple_datasets([
            {"name": "Dataset 1", "num_conversations": 2, "router_intent": "Lower BioAge Score"},
            {"name": "Dataset 2", "num_conversations": 3, "router_intent": "Lower BioAge Score"}
        ])
        
        # Initialize session state
        self.mock_session_state['datasets'] = self.datasets
        self.mock_session_state['current_dataset_index'] = 0
        self.mock_session_state['current_conversation_index'] = 0
        self.mock_session_state['current_router_intent'] = "Lower BioAge Score"
        
        # Create selector
        self.selector = ConversationSelector()
        
    def tearDown(self):
        """Clean up after each test"""
        self.patcher.stop()
        
    def test_init_session_state(self):
        """Test initialization of session state"""
        # Clear session state
        self.mock_session_state.clear()
        
        # Create new selector which should initialize state
        selector = ConversationSelector()
        
        # Verify state initialization
        self.assertIn('datasets', self.mock_session_state)
        self.assertIn('current_dataset_index', self.mock_session_state)
        self.assertIn('current_conversation_index', self.mock_session_state)
        
    def test_dataset_selection_changes_conversation(self):
        """Test that selecting a different dataset updates the conversation"""
        # Mock streamlit selectbox
        with patch('streamlit.selectbox') as mock_selectbox:
            # Simulate selecting Dataset 2
            mock_selectbox.return_value = "Dataset 2"
            
            # Handle selection
            self.selector.handle_dataset_selection()
            
            # Verify state updates
            self.assertEqual(self.mock_session_state['current_dataset_index'], 1)
            self.assertEqual(self.mock_session_state['current_conversation_index'], 0)
                
    def test_first_turn_selected_on_dataset_change(self):
        """Test that the first turn is automatically selected when changing datasets"""
        # Set initial state
        self.mock_session_state['current_dataset_index'] = 0
        self.mock_session_state['current_conversation_index'] = 1
        
        # Mock streamlit selectbox
        with patch('streamlit.selectbox') as mock_selectbox:
            # Simulate selecting Dataset 2
            mock_selectbox.return_value = "Dataset 2"
            
            # Handle selection
            self.selector.handle_dataset_selection()
            
            # Verify conversation index was reset
            self.assertEqual(self.mock_session_state['current_conversation_index'], 0)
                
    def test_get_current_conversation(self):
        """Test that get_current_conversation returns the correct conversation"""
        # Set indices
        self.mock_session_state['current_dataset_index'] = 1
        self.mock_session_state['current_conversation_index'] = 1
        
        # Get conversation
        conversation = self.selector.get_current_conversation()
        
        # Verify it's the correct conversation
        self.assertEqual(
            conversation,
            self.datasets[1].test_cases[1]
        )

if __name__ == '__main__':
    unittest.main() 