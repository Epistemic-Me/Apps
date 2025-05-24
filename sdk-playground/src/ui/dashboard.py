import streamlit as st
import plotly.graph_objects as go
from typing import List, Dict, Optional
from dataclasses import dataclass

from src.ui.components.conversation_turn import (
    render_conversation_sidebar,
    TurnMetricsSummary
)

# Page config must be the first Streamlit command
st.set_page_config(layout="wide", page_title="Dashboard")

class Dashboard:
    def __init__(self):
        if 'current_turn_id' not in st.session_state:
            st.session_state.current_turn_id = None
        if 'current_dataset' not in st.session_state:
            st.session_state.current_dataset = None
        if 'evaluation_status' not in st.session_state:
            st.session_state.evaluation_status = {}

    def render_metrics_overview(self, metrics: Dict[str, float], is_calculating: bool = False):
        """Render the main metrics visualization"""
        st.subheader("Conversation Metrics")
        
        if is_calculating:
            st.spinner("Calculating metrics...")
            return
            
        # Create radar chart for metrics
        fig = go.Figure(data=go.Scatterpolar(
            r=list(metrics.values()),
            theta=list(metrics.keys()),
            fill='toself'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1]
                )),
            showlegend=False,
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)

    def render_belief_system(self, beliefs: Dict[str, float], title: str):
        """Render a belief system with expandable details"""
        st.write(title)
        
        # Show top beliefs
        sorted_beliefs = sorted(beliefs.items(), key=lambda x: x[1], reverse=True)
        for belief, confidence in sorted_beliefs[:4]:
            st.progress(confidence, text=belief)
            
        # Show all beliefs in modal
        if st.button(f"View All {title}", key=f"view_all_{title}"):
            with st.modal(title):
                for belief, confidence in sorted_beliefs:
                    st.progress(confidence, text=belief)

    def render_main_view(self, conversation, current_turn):
        """Render the main conversation view"""
        if not current_turn:
            st.info("Select a turn from the sidebar to view details")
            return

        # Display learning objective
        st.header("Learning Objective")
        st.write(conversation.context.learning_objectives[0])

        # Coach and User sections
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Coach")
            st.write(current_turn.coach_message)
            if hasattr(current_turn, 'coach_beliefs'):
                self.render_belief_system(current_turn.coach_beliefs, "Coach's Belief Model")

        with col2:
            st.subheader("User")
            st.write(current_turn.user_message)
            if hasattr(current_turn, 'user_beliefs'):
                self.render_belief_system(current_turn.user_beliefs, "User's Belief Model")

    def render(self, conversation, available_datasets: List[str]):
        """Main render method for the dashboard"""
        if not conversation or not conversation.turns:
            st.warning("No conversation data available")
            return
        
        # Ensure we have a valid turn selected
        if not st.session_state.current_turn_id or st.session_state.current_turn_id not in {turn.id for turn in conversation.turns}:
            st.session_state.current_turn_id = conversation.turns[0].id
        
        # Main layout
        main_col, sidebar_col = st.columns([7, 3])

        with sidebar_col:
            # Tabs for Interactions and Evaluations
            tab1, tab2 = st.tabs(["Interactions", "Evaluations"])
            
            with tab1:
                render_conversation_sidebar(
                    turns=conversation.turns,
                    current_turn_id=st.session_state.current_turn_id,
                    on_turn_selected=lambda turn_id: self.handle_turn_selection(turn_id)
                )
            
            with tab2:
                self.render_metrics_overview(
                    conversation.metrics.to_dict(),
                    is_calculating='metrics' in st.session_state.evaluation_status
                )

        with main_col:
            current_turn = next(
                (turn for turn in conversation.turns 
                 if turn.id == st.session_state.current_turn_id),
                None
            )
            if current_turn:
                self.render_main_view(conversation, current_turn)
            else:
                st.info("Select a turn from the sidebar to view details")

    def handle_turn_selection(self, turn_id: str):
        """Handle turn selection in the sidebar"""
        st.session_state.current_turn_id = turn_id 

# --- Add main block for standalone Streamlit run ---
if __name__ == "__main__":
    from src.data.dataset_generator import DatasetGenerator
    from src.models.conversation import Conversation

    # Initialize session state if needed
    if 'datasets' not in st.session_state:
        generator = DatasetGenerator()
        datasets = generator.generate_multiple_datasets([
            {"name": "Sample Dataset", "num_conversations": 1}
        ])
        st.session_state.datasets = datasets
        st.session_state.current_dataset_index = 0
        st.session_state.current_conversation_index = 0

    # Get current dataset and conversation
    current_dataset = st.session_state.datasets[st.session_state.current_dataset_index]
    conversation = None
    if hasattr(current_dataset, 'test_cases') and current_dataset.test_cases:
        # Convert test case to Conversation model if needed
        from src.models.conversation import Turn, ConversationMetrics
        from src.models.context import EvaluationContext
        test_case = current_dataset.test_cases[0]
        # Minimal conversion for demo
        turns = []
        for i in range(2):
            turns.append(Turn(
                id=f"turn_{i}",
                coach_message=f"Coach message {i}",
                user_message=f"User message {i}",
                belief_updates={"old": {}, "new": {}},
                timestamp=0.0
            ))
        context = EvaluationContext(
            user_cohort="demo_cohort",
            router_intent="Demo Intent",
            belief_system={},
            demographic_data={},
            session_history=[],
            learning_objectives=["Demo objective"],
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
            id="conv_0",
            turns=turns,
            context=context,
            metrics=metrics
        )

    available_datasets = [d.name for d in st.session_state.datasets]
    dashboard = Dashboard()
    dashboard.render(conversation, available_datasets) 