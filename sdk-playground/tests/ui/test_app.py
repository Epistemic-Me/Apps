import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import streamlit as st
from deepeval.dataset import EvaluationDataset
import unittest
import ast
import asyncio

# Patch streamlit.set_page_config before importing app
with patch('streamlit.set_page_config') as mock_config:
    from src.ui.app import init_session_state, main, render_dataset_selector

from tests.ui.test_utils import SessionStateMock, create_llm_test_case, create_conversational_test_case

@pytest.fixture
def mock_streamlit():
    """Mock streamlit functions"""
    with patch('streamlit.session_state', new=SessionStateMock()):
        yield {
            'session_state': st.session_state
        }

@pytest.fixture
def mock_dataset():
    """Create a mock dataset for testing"""
    # Create test turns using LLMTestCase
    turns1 = [
        create_llm_test_case(
            input_text="How can I improve my health?",
            output_text="",
            context=[]
        ),
        create_llm_test_case(
            input_text="",
            output_text="I can help you analyze your health data.",
            context=[]
        ),
        create_llm_test_case(
            input_text="What's my biological age?",
            output_text="",
            context=[]
        )
    ]
    
    turns2 = [
        create_llm_test_case(
            input_text="What exercises should I do?",
            output_text="",
            context=[]
        ),
        create_llm_test_case(
            input_text="",
            output_text="Let me recommend some exercises based on your goals.",
            context=[]
        )
    ]
    
    dataset = EvaluationDataset(test_cases=[
        create_conversational_test_case(turns=turns1, chatbot_role="health_coach"),
        create_conversational_test_case(turns=turns2, chatbot_role="health_coach")
    ])
    dataset.name = "Test Dataset"
    return dataset

@patch('src.ui.app.DatasetGenerator')
@patch('src.ui.app.st')
def test_init_session_state(mock_st, mock_generator_class):
    """Test initialization of session state"""
    # Create test datasets with router intents
    dataset_configs = [
        {
            "name": "Health Conscious Professionals",
            "num_conversations": 3,
            "router_intent": "Lower BioAge Score"
        },
        {
            "name": "Fitness Enthusiasts",
            "num_conversations": 3,
            "router_intent": "Query Health Analysis"
        },
        {
            "name": "Wellness Beginners",
            "num_conversations": 3,
            "router_intent": "Research Health"
        }
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

@pytest.mark.asyncio
@patch('src.ui.app.MainLayout')
async def test_main_function(mock_layout_class, mock_streamlit):
    """Test main function"""
    # Create a mock instance
    mock_instance = MagicMock()
    mock_layout_class.return_value = mock_instance
    
    # Call main function
    await main()
    
    # Verify MainLayout was instantiated
    mock_layout_class.assert_called_once()

@pytest.mark.asyncio
@patch('src.ui.app.st')
@patch('src.ui.app.DatasetGenerator')
async def test_render_dataset_selector(mock_generator_class, mock_st, mock_dataset):
    """Test dataset selector rendering and state updates"""
    # Setup mock state
    mock_st.session_state.datasets = [mock_dataset]
    mock_st.session_state.current_dataset_index = 0
    mock_st.session_state.current_router_intent = "Lower BioAge Score"
    
    # Setup sidebar mocks
    mock_sidebar = MagicMock()
    mock_st.sidebar.header = MagicMock()
    mock_st.sidebar.selectbox = MagicMock()
    mock_st.sidebar.selectbox.side_effect = ["Test Dataset", "Query Health Analysis"]
    
    # Call function
    render_dataset_selector()
    
    # Verify sidebar header and selectboxes were called
    mock_st.sidebar.header.assert_called_once_with("Dataset Configuration")
    assert mock_st.sidebar.selectbox.call_count == 2
    
    # Verify state updates when router intent changes
    assert mock_st.session_state.current_router_intent == "Query Health Analysis"
    mock_generator_class.return_value.generate_evaluation_dataset.assert_called_once()

@pytest.mark.asyncio
@patch('src.ui.app.st')
async def test_navigation_buttons(mock_st, mock_dataset):
    """Test conversation navigation buttons"""
    # Setup mock state
    mock_st.session_state.current_conversation_index = 1  # Start at index 1 to allow previous navigation
    mock_st.session_state.datasets = [mock_dataset]
    mock_st.session_state.current_dataset_index = 0
    mock_st.session_state.current_router_intent = "Lower BioAge Score"

    # Mock dataset name to match selectbox
    mock_dataset.name = "Health Conscious Professionals"

    # Setup sidebar mocks
    mock_st.sidebar.selectbox.side_effect = ["Health Conscious Professionals", "Lower BioAge Score"]

    # Setup column mocks
    mock_col1, mock_col2 = MagicMock(), MagicMock()
    mock_st.columns.return_value = [mock_col1, mock_col2]

    # Setup navigation column mocks
    mock_nav_col1, mock_nav_col2 = MagicMock(), MagicMock()
    mock_col1.columns.return_value = [mock_nav_col1, mock_nav_col2]

    # Mock the test case length check
    mock_dataset.test_cases = [MagicMock() for _ in range(3)]  # Create 3 mock test cases

    # Mock context managers for main columns
    mock_col1.__enter__ = MagicMock(return_value=mock_col1)
    mock_col1.__exit__ = MagicMock(return_value=None)
    mock_col2.__enter__ = MagicMock(return_value=mock_col2)
    mock_col2.__exit__ = MagicMock(return_value=None)

    # Mock context managers for navigation columns
    mock_nav_col1.__enter__ = MagicMock(return_value=mock_nav_col1)
    mock_nav_col1.__exit__ = MagicMock(return_value=None)
    mock_nav_col2.__enter__ = MagicMock(return_value=mock_nav_col2)
    mock_nav_col2.__exit__ = MagicMock(return_value=None)

    # Mock container context manager
    mock_container = MagicMock()
    mock_container.__enter__ = MagicMock(return_value=mock_container)
    mock_container.__exit__ = MagicMock(return_value=None)
    mock_st.container.return_value = mock_container

    # Mock the button click
    button_clicked = False
    def mock_button(*args, **kwargs):
        nonlocal button_clicked
        if kwargs.get('key') == 'prev' and not button_clicked:
            button_clicked = True
            mock_st.session_state.current_conversation_index = 0  # Set directly to 0
            mock_st.rerun.return_value = None  # Mock rerun to do nothing
            mock_st.rerun.called = True  # Mark rerun as called
            return True
        return False

    mock_st.button = MagicMock(side_effect=mock_button)

    # Call main function
    await main()

    # Verify that the button was called with the correct key at least once
    assert any(call.args == ("← Previous",) and call.kwargs.get('key') == 'prev' 
               for call in mock_st.button.call_args_list), "Previous button was not called"

    # Verify that the session state was updated and rerun was called
    assert mock_st.session_state.current_conversation_index == 0
    assert mock_st.rerun.called

@pytest.mark.asyncio
@patch('src.ui.app.st')
@patch('src.ui.components.conversation_turn.render_conversation_turn')
async def test_conversation_display(mock_render_turn, mock_st, mock_dataset):
    """Test conversation turn display and selection"""
    # Setup mock state
    mock_st.session_state.current_conversation_index = 0
    mock_st.session_state.datasets = [mock_dataset]
    mock_st.session_state.current_dataset_index = 0
    mock_st.session_state.selected_turn_index = None
    mock_st.session_state.current_router_intent = "Lower BioAge Score"

    # Mock dataset name to match selectbox
    mock_dataset.name = "Health Conscious Professionals"

    # Setup sidebar mocks
    mock_st.sidebar.selectbox.side_effect = ["Health Conscious Professionals", "Lower BioAge Score"]

    # Setup columns mock
    mock_col1, mock_col2 = MagicMock(), MagicMock()
    mock_st.columns.return_value = [mock_col1, mock_col2]

    # Setup navigation column mocks
    mock_nav_col1, mock_nav_col2 = MagicMock(), MagicMock()
    mock_col1.columns.return_value = [mock_nav_col1, mock_nav_col2]

    # Setup container mock
    mock_container = MagicMock()
    mock_st.container.return_value.__enter__.return_value = mock_container

    # Mock button click for turn selection
    mock_container.button.return_value = True

    # Call main function
    await main()

    # Verify that render_conversation_turn was called
    assert mock_render_turn.called

@pytest.mark.asyncio
@patch('src.ui.app.st')
@patch('src.ui.app.EvaluationService')
async def test_evaluation_button(mock_eval_service, mock_st, mock_dataset):
    """Test evaluation button functionality and error handling"""
    # Setup mock state and services
    mock_st.session_state.current_conversation_index = 0
    mock_st.session_state.datasets = [mock_dataset]
    mock_st.session_state.current_dataset_index = 0
    mock_st.session_state.current_router_intent = "Lower BioAge Score"

    # Mock dataset name to match selectbox
    mock_dataset.name = "Health Conscious Professionals"

    # Setup sidebar mocks
    mock_st.sidebar.selectbox.side_effect = ["Health Conscious Professionals", "Lower BioAge Score"]

    # Setup columns mock
    mock_col1, mock_col2 = MagicMock(), MagicMock()
    mock_st.columns.return_value = [mock_col1, mock_col2]

    # Setup navigation column mocks
    mock_nav_col1, mock_nav_col2 = MagicMock(), MagicMock()
    mock_col1.columns.return_value = [mock_nav_col1, mock_nav_col2]

    # Setup spinner context
    mock_spinner = MagicMock()
    mock_st.spinner.return_value.__enter__.return_value = mock_spinner

    # Mock successful evaluation
    mock_eval_instance = MagicMock()
    mock_eval_instance.evaluation_cost = 0.05
    mock_eval_instance.evaluate_conversation = AsyncMock(return_value={
        'User Identification': 0.8,
        'Belief Evidencing': 0.7,
        'Belief Verification': 0.9
    })
    mock_eval_service.return_value = mock_eval_instance

    # Mock evaluation button click
    def button_side_effect(*args, **kwargs):
        if kwargs.get('key') == 'eval':
            return True
        return False

    mock_col2.button.side_effect = button_side_effect

    # Call main function
    await main()

    # Verify that evaluation was attempted
    assert mock_eval_instance.evaluate_conversation.called

@pytest.mark.asyncio
@patch('src.ui.app.st')
@patch('src.ui.app.EvaluationService')
async def test_evaluation_error_handling(mock_eval_service, mock_st, mock_dataset):
    """Test evaluation error handling"""
    # Setup mock state and services
    mock_st.session_state.current_conversation_index = 0
    mock_st.session_state.datasets = [mock_dataset]
    mock_st.session_state.current_dataset_index = 0
    mock_st.session_state.current_router_intent = "Lower BioAge Score"

    # Mock dataset name to match selectbox
    mock_dataset.name = "Health Conscious Professionals"

    # Setup sidebar mocks
    mock_st.sidebar.selectbox.side_effect = ["Health Conscious Professionals", "Lower BioAge Score"]

    # Setup columns mock
    mock_col1, mock_col2 = MagicMock(), MagicMock()
    mock_st.columns.return_value = [mock_col1, mock_col2]

    # Setup navigation column mocks
    mock_nav_col1, mock_nav_col2 = MagicMock(), MagicMock()
    mock_col1.columns.return_value = [mock_nav_col1, mock_nav_col2]

    # Setup error scenario
    mock_eval_instance = MagicMock()
    mock_eval_instance.evaluate_conversation = AsyncMock(side_effect=Exception("API Error"))
    mock_eval_service.return_value = mock_eval_instance

    # Mock evaluation button click
    def button_side_effect(*args, **kwargs):
        if kwargs.get('key') == 'eval':
            return True
        return False

    mock_col2.button.side_effect = button_side_effect

    # Call main function
    await main()

    # Verify that error was displayed with double wrapping (from both main_layout.py and app.py)
    mock_st.error.assert_called_with('Evaluation failed: Evaluation failed: API Error')

if __name__ == '__main__':
    unittest.main() 