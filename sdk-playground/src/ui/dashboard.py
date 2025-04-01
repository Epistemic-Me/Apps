import streamlit as st
import plotly.graph_objects as go
from typing import List, Dict, Optional
from dataclasses import dataclass

from .components.conversation_turn import (
    render_conversation_sidebar,
    TurnMetricsSummary
)

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