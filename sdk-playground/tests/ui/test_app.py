import pytest
from unittest.mock import patch, MagicMock
import streamlit as st
from deepeval.dataset import EvaluationDataset
import unittest
import ast

# Patch streamlit.set_page_config before importing app
with patch('streamlit.set_page_config') as mock_config:
    from src.app import init_session_state, main
    
from tests.ui.test_utils import SessionStateMock, create_llm_test_case, create_conversational_test_case

@pytest.fixture
def mock_streamlit():
    """Mock streamlit functions"""
    with patch('streamlit.session_state', new=SessionStateMock()):
        yield {
            'session_state': st.session_state
        }

@patch('src.app.DatasetGenerator')
@patch('src.app.st')
def test_init_session_state(mock_st, mock_generator_class):
    """Test initialization of session state"""
    # Create test datasets
    dataset_configs = [
        {"name": "Health Conscious Professionals", "num_conversations": 3},
        {"name": "Fitness Enthusiasts", "num_conversations": 3},
        {"name": "Wellness Beginners", "num_conversations": 3}
    ]
    
    # Create mock datasets
    mock_datasets = []
    for config in dataset_configs:
        dataset = EvaluationDataset(test_cases=[])
        dataset.name = config["name"]
        mock_datasets.append(dataset)
    
    # Setup mock generator
    mock_generator = MagicMock()
    mock_generator.generate_multiple_datasets.return_value = mock_datasets
    mock_generator_class.return_value = mock_generator
    
    # Mock session state
    mock_session_state = SessionStateMock()
    mock_session_state._state = {}  # Clear any default state
    mock_st.session_state = mock_session_state
    
    # Initialize session state
    init_session_state()
    
    # Verify that datasets were generated correctly
    assert len(mock_st.session_state.datasets) == len(dataset_configs)
    for actual_dataset, expected_dataset in zip(mock_st.session_state.datasets, mock_datasets):
        assert actual_dataset.name == expected_dataset.name
    assert mock_st.session_state.current_dataset_index == 0
    assert mock_st.session_state.current_conversation_index == 0
    
    # Verify the generator was called with correct parameters
    mock_generator.generate_multiple_datasets.assert_called_once_with(dataset_configs)

@patch('src.app.MainLayout')
def test_main_function(mock_layout_class, mock_streamlit):
    """Test main function"""
    # Create a mock instance
    mock_instance = MagicMock()
    mock_layout_class.return_value = mock_instance
    
    # Call main function
    main()
    
    # Verify MainLayout was instantiated and render was called
    mock_layout_class.assert_called_once()
    mock_instance.render.assert_called_once()

def test_page_config_first_command(mock_streamlit):
    """Test that set_page_config is called before any other Streamlit command"""
    with patch('src.ui.components.main_layout.MainLayout') as mock_layout, \
         patch('streamlit.markdown') as mock_markdown:
        # Call main function
        main()
        
        # If markdown was called, verify it was after set_page_config
        if mock_markdown.called:
            assert mock_markdown.call_args_list[0] > mock_config.call_args_list[0] 

class TestAppConfiguration(unittest.TestCase):
    def test_page_config_placement(self):
        """Test that st.set_page_config is called exactly once and before other Streamlit commands"""
        with open('src/ui/app.py', 'r') as file:
            content = file.read()
            tree = ast.parse(content)
            
            # Find all st.set_page_config calls
            page_config_calls = []
            streamlit_calls = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Attribute):
                        # Check if it's a streamlit call (st.something)
                        if isinstance(node.func.value, ast.Name) and node.func.value.id == 'st':
                            if node.func.attr == 'set_page_config':
                                page_config_calls.append(node.lineno)
                            else:
                                streamlit_calls.append(node.lineno)
            
            # Verify there's exactly one set_page_config call
            self.assertEqual(len(page_config_calls), 1, 
                           "st.set_page_config should be called exactly once")
            
            # Verify it's called before any other Streamlit commands
            first_config_call = page_config_calls[0]
            other_calls_before = [line for line in streamlit_calls if line < first_config_call]
            self.assertEqual(len(other_calls_before), 0,
                           "st.set_page_config must be the first Streamlit command")

if __name__ == '__main__':
    unittest.main() 