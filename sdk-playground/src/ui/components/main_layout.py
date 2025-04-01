import streamlit as st
from typing import List, Optional
from dataclasses import dataclass
import asyncio
import ast

from deepeval.test_case import ConversationalTestCase, LLMTestCase
from deepeval.dataset import EvaluationDataset

from src.ui.components.conversation_selector import ConversationSelector
from src.ui.components.conversation_turn import render_conversation_turn
from src.ui.components.metrics_display import MetricsDisplay
from src.ui.components.context_viewer import ContextViewer
from src.models.conversation import Turn, ConversationMetrics
from src.services.evaluation import EvaluationService

@dataclass
class MainLayout:
    def __init__(self, evaluation_service: Optional[EvaluationService] = None):
        """Initialize the main layout and components
        
        Args:
            evaluation_service: Optional evaluation service instance. If not provided,
                              a new instance will be created in mock mode.
        """
        self.selector = ConversationSelector()
        self.metrics_display = MetricsDisplay()
        self.context_viewer = ContextViewer()
        self.evaluation_service = evaluation_service or EvaluationService(use_mock=True)
        
        # Initialize session state for UI
        if 'current_turn_id' not in st.session_state:
            st.session_state.current_turn_id = None
        if 'evaluation_results' not in st.session_state:
            st.session_state.evaluation_results = None

    def convert_test_case_to_turns(self, test_case: ConversationalTestCase) -> List[Turn]:
        """Convert a ConversationalTestCase to a list of Turns"""
        turns = []
        for i, turn in enumerate(test_case.turns):
            # Create Turn object from test case
            turns.append(Turn(
                id=f"turn_{i}",
                user_message=turn.input,  # User's message
                coach_message=turn.actual_output,  # Coach's response
                belief_updates={
                    "old": {},  # Would need to extract from context if available
                    "new": {}
                },
                timestamp=0.0  # Would need to extract from context if available
            ))
        return turns

    def extract_context_from_test_case(self, test_case: ConversationalTestCase) -> dict:
        """Extract context dictionary from test case"""
        # Get context from the first turn if available
        if not test_case.turns:
            return {}
            
        # Try to get context from the first turn
        context = test_case.turns[0].context
        if not context:
            return {}
            
        # Parse context strings into a dictionary
        result = {}
        context_strings = context if isinstance(context, list) else [context]
        
        for line in context_strings:
            if isinstance(line, str) and ": " in line:
                key, value = line.split(": ", 1)
                key = key.lower().replace(" ", "_")
                
                # Handle different value types
                if key == "belief_system":
                    # Parse belief system string into dictionary
                    beliefs = {}
                    for belief in value.split(", "):
                        if ": " in belief:
                            b_key, b_value = belief.split(": ")
                            beliefs[b_key] = float(b_value)
                    value = beliefs
                elif key == "session_history":
                    # Parse session history string into list of dictionaries
                    try:
                        # Remove brackets and split by comma
                        value = value.strip('[]')
                        # Convert string representation of dict to actual dict
                        value = [ast.literal_eval(value)]
                    except (ValueError, SyntaxError):
                        value = []
                elif key in ["learning_objectives", "topics_covered"]:
                    # Parse list string into actual list
                    try:
                        # Remove brackets and split by comma
                        value = value.strip('[]')
                        # Split by comma and clean up each item
                        value = [item.strip() for item in value.split(',')]
                    except (ValueError, AttributeError):
                        value = []
                elif key == "confidence_scores":
                    # Parse confidence scores string into dictionary
                    scores = {}
                    for score in value.split(", "):
                        if ": " in score:
                            s_key, s_value = score.split(": ")
                            scores[s_key] = float(s_value)
                    value = scores
                elif key == "demographics":
                    value = value.split(", ")
                
                result[key] = value
                
        return result

    async def run_evaluation(self, conversation: ConversationalTestCase):
        """Run evaluation on the current conversation
        
        Args:
            conversation: The conversation test case to evaluate
            
        Returns:
            dict: Evaluation metrics if successful, None if failed
        """
        try:
            # Run evaluation using the service
            results = await self.evaluation_service.evaluate_conversation(conversation)
            
            if results:
                # Store results in session state
                st.session_state.evaluation_results = results
                
                # Update metrics for each turn
                turns = self.convert_test_case_to_turns(conversation)
                for turn in turns:
                    turn.metrics = {
                        'User Identification': results.get('User Identification', 0.0),
                        'Belief Evidencing': results.get('Belief Evidencing', 0.0),
                        'Belief Verification': results.get('Belief Verification', 0.0)
                    }
                
                return results
            return None
            
        except Exception as e:
            raise Exception(f"Evaluation failed: {str(e)}")

    async def render(self):
        """Main render method for the application layout"""
        # Render sidebar with conversation selector
        self.selector.render()
        
        # Get current conversation
        current_conversation = self.selector.get_current_conversation()
        if not current_conversation:
            st.warning("Please select a dataset and conversation to begin")
            return
            
        # Convert test case to turns and extract context
        turns = self.convert_test_case_to_turns(current_conversation)
        context = self.extract_context_from_test_case(current_conversation)
        
        # Main content area
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Conversation view
            st.markdown("## Conversation")
            for turn in turns:
                render_conversation_turn(
                    turn=turn,
                    is_selected=turn.id == st.session_state.current_turn_id
                )
            
            # Evaluation section
            st.markdown("## Evaluation")
            if st.button("Run Evaluation"):
                results = await self.run_evaluation(current_conversation)
                
            # Display evaluation results if available
            if st.session_state.evaluation_results:
                # Create a dedicated section for metrics
                st.markdown("### Metrics")
                metrics_col1, metrics_col2 = st.columns([2, 1])
                
                with metrics_col1:
                    self.metrics_display.render_radar_chart(st.session_state.evaluation_results)
                
                with metrics_col2:
                    # Display summary metrics
                    metrics = st.session_state.evaluation_results
                    avg_score = sum(metrics.values()) / len(metrics)
                    st.metric("Average Score", f"{avg_score:.2f}")
                    
                    best_metric = max(metrics.items(), key=lambda x: x[1])
                    st.metric(
                        "Strongest Area",
                        f"{best_metric[0].replace('_', ' ').title()}",
                        f"{best_metric[1]:.2f}"
                    )
                    
                    worst_metric = min(metrics.items(), key=lambda x: x[1])
                    st.metric(
                        "Area for Improvement",
                        f"{worst_metric[0].replace('_', ' ').title()}",
                        f"{worst_metric[1]:.2f}"
                    )
                
                # Display detailed metrics table
                self.metrics_display.render_metrics_table(st.session_state.evaluation_results)
                
                # Display cost if not in mock mode
                if not self.evaluation_service.use_mock:
                    st.write(f"Evaluation cost: ${self.evaluation_service.evaluation_cost:.4f}")
            
        with col2:
            # Context viewer
            st.markdown("## Context")
            self.context_viewer.render(context) 