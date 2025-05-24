import streamlit as st
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ContextViewer:
    def render_belief_system(self, beliefs: Dict[str, float]):
        """Render belief system as a bar chart"""
        if not beliefs:
            return

        st.markdown("### Belief System")
        
        # Convert beliefs to percentage for better visualization
        for belief, value in beliefs.items():
            label = belief.replace("_", " ").title()
            st.progress(value, text=f"{label}: {value:.0%}")

    def render_session_history(self, sessions: List[Dict]):
        """Render session history as a timeline"""
        if not sessions:
            return

        st.markdown("### Session History")
        
        # Handle both single dictionary and list of dictionaries
        if isinstance(sessions, dict):
            sessions = [sessions]
        elif not isinstance(sessions, list):
            st.warning("Invalid session history format")
            return
        
        for session in sessions:
            if not isinstance(session, dict):
                continue
                
            session_id = session.get('session_id', 'Unknown')
            timestamp = session.get('timestamp')
            topics = session.get('topics_covered', [])
            engagement = session.get('engagement_score')
            
            with st.expander(f"Session {session_id}", expanded=True):
                if timestamp:
                    try:
                        time_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                        st.write(f"**Time:** {time_str}")
                    except (ValueError, TypeError):
                        st.write("**Time:** Unknown")
                
                if topics:
                    st.write("**Topics Covered:**")
                    for topic in topics:
                        st.markdown(f"- {str(topic).replace('_', ' ').title()}")
                
                if engagement is not None:
                    try:
                        st.metric("Engagement Score", f"{float(engagement):.0%}")
                    except (ValueError, TypeError):
                        st.metric("Engagement Score", "Unknown")

    def render_learning_objectives(self, objectives: List[str]):
        """Render learning objectives as a checklist"""
        if not objectives:
            return

        st.markdown("### Learning Objectives")
        for objective in objectives:
            st.checkbox(objective.replace("_", " ").title(), value=False, disabled=True)

    def render_confidence_scores(self, scores: Dict[str, float]):
        """Render confidence scores with gauges"""
        if not scores:
            return

        st.markdown("### Confidence Scores")
        cols = st.columns(len(scores))
        
        for col, (metric, value) in zip(cols, scores.items()):
            with col:
                st.metric(
                    metric.replace("_", " ").title(),
                    f"{value:.0%}"
                )

    def render_demographic_data(self, demographics: Dict[str, str]):
        """Render demographic data in a clean format"""
        if not demographics:
            return

        st.markdown("### Demographics")
        cols = st.columns(len(demographics))
        
        for col, (key, value) in zip(cols, demographics.items()):
            with col:
                st.metric(
                    key.replace("_", " ").title(),
                    value
                )

    def render(self, context: Optional[Dict] = None):
        """Main render method for the context viewer"""
        st.markdown("## Evaluation Context")
        
        if not context:
            st.warning("No context available")
            return

        # User cohort and router intent as headers
        st.subheader(f"User Cohort: {context.get('user_cohort', 'Unknown').replace('_', ' ').title()}")
        st.subheader(f"Router Intent: {context.get('router_intent', 'Unknown')}")
        
        # Create tabs for different context sections
        tab1, tab2, tab3 = st.tabs(["Beliefs & Objectives", "Session History", "User Profile"])
        
        with tab1:
            self.render_belief_system(context.get("belief_system"))
            st.divider()
            self.render_learning_objectives(context.get("learning_objectives"))
            
        with tab2:
            self.render_session_history(context.get("session_history"))
            
        with tab3:
            self.render_demographic_data(context.get("demographic_data"))
            st.divider()
            self.render_confidence_scores(context.get("confidence_scores")) 