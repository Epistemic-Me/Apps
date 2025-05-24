import unittest
from unittest.mock import MagicMock, patch
import streamlit as st
import sys
from pathlib import Path
from typing import List, Dict

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

from deepeval.dataset import EvaluationDataset
from deepeval.test_case import ConversationalTestCase, LLMTestCase

from src.ui.components.conversation_selector import ConversationSelector
from src.data.dataset_generator import DatasetGenerator

class TestConversationSelector(unittest.TestCase):
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
        
    def test_initialization(self):
        """Test selector initialization"""
        # Verify session state initialization
        self.assertIn('datasets', self.mock_session_state)
        self.assertIn('current_dataset_index', self.mock_session_state)
        self.assertIn('current_conversation_index', self.mock_session_state)
        
    def test_dataset_selection(self):
        """Test dataset selection updates state"""
        # Mock streamlit selectbox
        with patch('streamlit.selectbox') as mock_selectbox:
            # Simulate selecting second dataset
            mock_selectbox.return_value = "Dataset 2"
            
            # Handle selection
            self.selector.handle_dataset_selection()
            
            # Verify state updates
            self.assertEqual(self.mock_session_state['current_dataset_index'], 1)
            self.assertEqual(self.mock_session_state['current_conversation_index'], 0)
            
    def test_conversation_selection(self):
        """Test conversation selection updates state"""
        # Set up current dataset
        current_dataset = self.datasets[0]
        self.mock_session_state['current_dataset_index'] = 0
        
        # Mock streamlit selectbox
        with patch('streamlit.selectbox') as mock_selectbox:
            # Simulate selecting second conversation
            mock_selectbox.return_value = 1
            
            # Handle selection
            self.selector.handle_conversation_selection()
            
            # Verify state update
            self.assertEqual(self.mock_session_state['current_conversation_index'], 1)
            
    def test_get_current_conversation(self):
        """Test getting current conversation"""
        # Set indices
        self.mock_session_state['current_dataset_index'] = 0
        self.mock_session_state['current_conversation_index'] = 1
        
        # Get current conversation
        conversation = self.selector.get_current_conversation()
        
        # Verify it's the correct conversation
        self.assertEqual(
            conversation,
            self.datasets[0].test_cases[1]
        )
        
    def test_render_selector(self):
        """Test rendering of selector components"""
        # Mock streamlit components
        with patch('streamlit.selectbox') as mock_selectbox:
            # Configure mock to return appropriate values
            mock_selectbox.side_effect = ["Dataset 1", 0]
            
            # Render selector
            self.selector.render()
            
            # Verify selectbox was called twice (once for dataset, once for conversation)
            self.assertEqual(mock_selectbox.call_count, 2)
            
    def test_dataset_change_resets_conversation(self):
        """Test that changing dataset resets conversation index"""
        # Set initial state
        self.mock_session_state['current_dataset_index'] = 0
        self.mock_session_state['current_conversation_index'] = 1
        
        # Mock streamlit selectbox
        with patch('streamlit.selectbox') as mock_selectbox:
            # Simulate selecting new dataset
            mock_selectbox.return_value = "Dataset 2"
            
            # Handle selection
            self.selector.handle_dataset_selection()
            
            # Verify conversation index was reset
            self.assertEqual(self.mock_session_state['current_conversation_index'], 0)
            
    def test_invalid_indices_handling(self):
        """Test handling of invalid indices"""
        # Set invalid indices
        self.mock_session_state['current_dataset_index'] = 99
        self.mock_session_state['current_conversation_index'] = 99
        
        # Get current conversation should handle this gracefully
        conversation = self.selector.get_current_conversation()
        
        # Should return first conversation of first dataset
        self.assertEqual(
            conversation,
            self.datasets[0].test_cases[0]
        )

if __name__ == '__main__':
    unittest.main() 