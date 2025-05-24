import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import streamlit as st
import sys

from src.ui.components.main_layout import MainLayout
from src.models.conversation import Turn
from deepeval.test_case import ConversationalTestCase, LLMTestCase
from tests.ui.test_utils import SessionStateMock, create_llm_test_case
from src.services.evaluation import EvaluationService

# Mock Streamlit modules to prevent warnings
mock_module = MagicMock()
mock_module.get_script_run_ctx = lambda: MagicMock(session_id='test_session')
mock_module.ScriptRunContext = MagicMock()

@pytest.fixture(autouse=True)
def mock_streamlit_context():
    with patch.dict('sys.modules', {
        'streamlit.runtime.scriptrunner': mock_module,
        'streamlit.runtime.scriptrunner.script_run_context': mock_module
    }):
        yield

@pytest.fixture
def mock_streamlit():
    """Mock streamlit functions"""
    with patch('streamlit.columns') as mock_cols, \
         patch('streamlit.markdown') as mock_md, \
         patch('streamlit.warning') as mock_warn, \
         patch('streamlit.session_state', new=SessionStateMock({'datasets': []})):
        yield {
            'columns': mock_cols,
            'markdown': mock_md,
            'warning': mock_warn
        }

@pytest.fixture
def mock_evaluation_service():
    """Mock evaluation service"""
    with patch('src.services.evaluation.EvaluationService') as mock_service:
        service = MagicMock()
        service.use_mock = True
        service.evaluate_conversation = AsyncMock(return_value={"metric1": 0.8, "metric2": 0.9})
        mock_service.return_value = service
        yield service

@pytest.fixture
def sample_test_case():
    """Create a sample test case for testing"""
    mock_turn = create_llm_test_case(
        input_text="Hello, how are you?",
        output_text="I'm doing well, thanks!",
        context=[
            "User Cohort: Health Conscious",
            "Belief System: health: 0.8, fitness: 0.7",
            "Session History: [{'session_id': 'test', 'timestamp': 1234567890, 'topics_covered': ['intro'], 'engagement_score': 0.9}]",
            "Learning Objectives: [stay healthy, exercise regularly]",
            "Confidence Scores: health: 0.8, fitness: 0.7"
        ]
    )
    test_case = ConversationalTestCase(turns=[mock_turn])
    return test_case

def test_main_layout_initialization():
    """Test MainLayout initialization"""
    with patch('streamlit.session_state', new=SessionStateMock({'datasets': []})):
        layout = MainLayout()
        assert layout.selector is not None
        assert layout.metrics_display is not None
        assert layout.context_viewer is not None

def test_convert_test_case_to_turns(sample_test_case):
    """Test conversion of test case to turns"""
    layout = MainLayout()
    turns = layout.convert_test_case_to_turns(sample_test_case)
    
    assert len(turns) == 1
    assert isinstance(turns[0], Turn)
    assert turns[0].coach_message == "Hello, how are you?"
    assert turns[0].user_message == "I'm doing well, thanks!"
    assert turns[0].id == "turn_0"

def test_extract_context_from_test_case(sample_test_case):
    """Test context extraction from test case"""
    layout = MainLayout()
    context = layout.extract_context_from_test_case(sample_test_case)
    
    assert context['user_cohort'] == "Health Conscious"
    assert context['belief_system'] == {'health': 0.8, 'fitness': 0.7}
    assert len(context['session_history']) == 1
    assert context['session_history'][0]['session_id'] == 'test'
    assert context['learning_objectives'] == ['stay healthy', 'exercise regularly']
    assert context['confidence_scores'] == {'health': 0.8, 'fitness': 0.7}

@pytest.mark.asyncio
async def test_render_no_conversation(mock_streamlit):
    """Test rendering when no conversation is selected"""
    layout = MainLayout()
    
    # Mock selector to return None for current conversation
    layout.selector.get_current_conversation = MagicMock(return_value=None)
    
    await layout.render()
    mock_streamlit['warning'].assert_called_once_with("Please select a dataset and conversation to begin")

@pytest.mark.asyncio
async def test_render_with_conversation(mock_streamlit, sample_test_case):
    """Test rendering with a selected conversation"""
    layout = MainLayout()

    # Mock selector to return a test case
    layout.selector.get_current_conversation = MagicMock(return_value=sample_test_case)
    layout.metrics_display.render = MagicMock()
    layout.context_viewer.render = MagicMock()

    # Mock the column layout
    mock_col1, mock_col2 = MagicMock(), MagicMock()
    mock_streamlit['columns'].return_value = [mock_col1, mock_col2]

    await layout.render()

    # Verify that the layout was rendered with the correct column calls
    assert mock_streamlit['columns'].call_count >= 1
    assert [2, 1] in [call.args[0] for call in mock_streamlit['columns'].call_args_list]
    
    # Verify that markdown was called with the conversation header
    assert any(call.args == ("## Conversation",) for call in mock_streamlit['markdown'].call_args_list)

def test_render_metrics_radar_chart(mock_streamlit):
    """Test rendering of the metrics radar chart"""
    layout = MainLayout()
    
    # Mock evaluation results with various values
    evaluation_results = {
        "User Identification": 0.85,
        "Belief Evidencing": 0.0,  # Edge case: minimum value
        "Belief Verification": 1.0,  # Edge case: maximum value
        "Learning Progress": 0.5
    }
    st.session_state.evaluation_results = evaluation_results
    
    with patch('plotly.graph_objects.Figure') as mock_figure, \
         patch('streamlit.plotly_chart') as mock_plotly:
        # Mock the plotly figure creation
        mock_fig = MagicMock()
        mock_figure.return_value = mock_fig
        
        # Render metrics
        layout.metrics_display.render_radar_chart(evaluation_results)
        
        # Verify chart was created with correct metrics
        mock_figure.assert_called_once()
        mock_plotly.assert_called_once_with(mock_fig, use_container_width=True)

def test_render_metrics_description(mock_streamlit):
    """Test rendering of metrics descriptions"""
    layout = MainLayout()
    
    evaluation_results = {
        "User Identification": 0.85,
        "Belief Evidencing": 0.75
    }
    st.session_state.evaluation_results = evaluation_results
    
    with patch('streamlit.table') as mock_table:
        # Render metrics
        layout.metrics_display.render_metrics_table(evaluation_results)
        
        # Verify descriptions were displayed
        mock_table.assert_called_once()
        assert mock_table.call_count >= 1

def test_render_invalid_metrics(mock_streamlit):
    """Test handling of invalid metric values"""
    layout = MainLayout()
    
    # Mock invalid evaluation results
    evaluation_results = {
        "User Identification": None,  # Invalid value
        "Belief Evidencing": -0.1,  # Out of range
        "Belief Verification": 1.5,  # Out of range
        "Invalid Metric": "not a number"  # Wrong type
    }
    st.session_state.evaluation_results = evaluation_results
    
    with patch('streamlit.warning') as mock_warning:
        # Render metrics
        layout.metrics_display.render(evaluation_results)
        
        # Verify warnings were shown for invalid values
        assert mock_warning.call_count >= 1
        warnings = [call.args[0] for call in mock_warning.call_args_list]
        assert any("Invalid metric value" in warning for warning in warnings)

def test_render_metrics_trend(mock_streamlit):
    """Test rendering of metrics trends over time"""
    layout = MainLayout()
    
    # Mock historical evaluation results
    historical_results = [
        {
            "timestamp": "2024-03-01",
            "metrics": {
                "User Identification": 0.75,
                "Belief Evidencing": 0.65
            }
        },
        {
            "timestamp": "2024-03-02",
            "metrics": {
                "User Identification": 0.85,
                "Belief Evidencing": 0.75
            }
        }
    ]
    
    with patch('streamlit.session_state', new=SessionStateMock({'historical_evaluation_results': historical_results})), \
         patch('plotly.graph_objects.Figure') as mock_figure, \
         patch('streamlit.plotly_chart') as mock_plotly:
        # Mock the plotly figure creation
        mock_fig = MagicMock()
        mock_figure.return_value = mock_fig
        
        # Render trends
        layout.metrics_display.render_trends(historical_results)
        
        # Verify trend chart was created
        mock_figure.assert_called_once()
        mock_plotly.assert_called_once_with(mock_fig, use_container_width=True)

@pytest.mark.asyncio
async def test_render_with_evaluation(mock_streamlit, sample_test_case, mock_evaluation_service):
    """Test rendering with evaluation button click"""
    layout = MainLayout()
    layout.evaluation_service = mock_evaluation_service

    # Mock selector to return a test case
    layout.selector.get_current_conversation = MagicMock(return_value=sample_test_case)
    layout.metrics_display.render = MagicMock()
    layout.context_viewer.render = MagicMock()

    # Mock the column layout and button
    mock_col1, mock_col2 = MagicMock(), MagicMock()
    mock_streamlit['columns'].return_value = [mock_col1, mock_col2]
    
    with patch('streamlit.button') as mock_button, \
         patch('streamlit.spinner') as mock_spinner, \
         patch('streamlit.metric') as mock_metric:
        
        # Simulate button click
        mock_button.return_value = True
        
        # Render the layout
        await layout.render()
        
        # Verify evaluation was called
        mock_evaluation_service.evaluate_conversation.assert_called_once_with(sample_test_case)
        
        # Verify results were displayed
        assert mock_metric.call_count >= 2  # At least two metrics should be displayed
        assert st.session_state.evaluation_results == {"metric1": 0.8, "metric2": 0.9}

@pytest.mark.asyncio
async def test_run_evaluation_from_ui(mock_streamlit, sample_test_case):
    """Test running evaluation from the UI button click"""
    layout = MainLayout()
    
    # Mock selector to return a test case
    layout.selector.get_current_conversation = MagicMock(return_value=sample_test_case)
    
    # Mock evaluation results
    expected_results = {
        "User Identification": 0.85,
        "Belief Evidencing": 0.75,
        "Belief Verification": 0.90
    }
    
    # Mock the evaluation service to return a coroutine
    async def mock_evaluate(*args, **kwargs):
        return expected_results
    layout.evaluation_service.evaluate_conversation = AsyncMock(side_effect=mock_evaluate)
    
    # Mock the button click
    with patch('streamlit.button') as mock_button, \
         patch('streamlit.columns') as mock_columns:
        
        # Mock button click to trigger evaluation
        mock_button.return_value = True
        
        # Mock columns
        mock_col1, mock_col2 = MagicMock(), MagicMock()
        mock_columns.return_value = [mock_col1, mock_col2]
        
        # Render layout which should trigger evaluation
        await layout.render()
        
        # Verify evaluation was triggered
        layout.evaluation_service.evaluate_conversation.assert_called_once()
        
        # Verify results were stored in session state
        assert st.session_state.evaluation_results == expected_results

def test_main_layout_mock_mode():
    """Test that MainLayout uses mock mode by default"""
    with patch('streamlit.session_state', new=SessionStateMock({'datasets': []})):
        layout = MainLayout()
        assert layout.evaluation_service.use_mock is True
        
        # Test with custom evaluation service
        custom_service = EvaluationService(use_mock=False)
        layout_with_service = MainLayout(evaluation_service=custom_service)
        assert layout_with_service.evaluation_service.use_mock is False

if __name__ == '__main__':
    pytest.main([__file__]) 