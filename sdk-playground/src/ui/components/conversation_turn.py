from dataclasses import dataclass
from typing import Dict, Optional, List, Callable
import streamlit as st
import plotly.graph_objects as go

from src.models.conversation import Turn

@dataclass
class TurnMetricsSummary:
    metrics: Optional[Dict[str, float]] = None
    is_calculating: bool = False

    def render_indicator(self):
        """Render a small metrics visualization"""
        if self.is_calculating:
            st.spinner("Calculating metrics...")
            return
            
        if not self.metrics:
            return
            
        values = list(self.metrics.values())
        if not values:
            return
            
        fig = go.Figure(data=go.Scatter(
            y=values,
            mode='lines',
            line=dict(width=1, color='#90CAF9'),
            showlegend=False
        ))
        
        fig.update_layout(
            height=20,
            margin=dict(l=0, r=0, t=0, b=0),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            yaxis=dict(range=[0, 1], showgrid=False, zeroline=False, showticklabels=False),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
        )
        
        st.plotly_chart(fig, use_container_width=True)

def render_belief_diff(old_beliefs: Dict[str, float], new_beliefs: Dict[str, float]):
    """Render git-style diff of beliefs that changed"""
    changes = []
    for belief, new_value in new_beliefs.items():
        old_value = old_beliefs.get(belief, 0.0)
        if new_value != old_value:
            changes.append((belief, old_value, new_value))
    
    if changes:
        st.markdown("""
            <div class='chat-bubble coach-bubble' style='background-color: #2C2C2C; border: 1px solid #90CAF9; color: #90CAF9;'>
                <div class='chat-name'>Belief Updates</div>
                <div style='font-family: monospace;'>
        """, unsafe_allow_html=True)
        
        for belief, old_value, new_value in changes:
            # Format the belief name and values
            belief_name = belief.replace("_", " ").title()
            st.markdown(f"""
                <div style='margin: 4px 0;'>
                    <span style='color: #90CAF9'>→</span> {belief_name}:<br/>
                    <span style='color: #666'>{old_value:.2f}</span> → <span style='color: #A5D6A7'>{new_value:.2f}</span>
                </div>
            """, unsafe_allow_html=True)
            
        st.markdown("</div></div>", unsafe_allow_html=True)

def render_conversation_turn(
    turn: Turn,
    is_selected: bool = False,
    char_limit: int = 100
):
    """Render a single conversation turn with chat bubbles"""
    # Custom CSS for chat bubbles
    st.markdown("""
        <style>
        .chat-container {
            padding: 10px;
            border-radius: 8px;
            margin: 10px 0;
            background-color: #1E1E1E;
        }
        .chat-bubble {
            padding: 12px 16px;
            border-radius: 15px;
            margin: 8px 0;
            max-width: 80%;
            position: relative;
            line-height: 1.5;
            color: #1E1E1E;
        }
        .coach-bubble {
            background-color: #90CAF9;
            margin-right: auto;
            border-bottom-left-radius: 5px;
        }
        .user-bubble {
            background-color: #A5D6A7;
            margin-left: auto;
            border-bottom-right-radius: 5px;
            text-align: right;
        }
        .chat-name {
            font-size: 0.8em;
            margin-bottom: 4px;
            color: #90CAF9;
        }
        .selected-turn {
            background-color: #2C2C2C;
            border-left: 3px solid #90CAF9;
        }
        .user-name {
            color: #A5D6A7;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Container class with conditional selection highlighting
    container_class = "chat-container selected-turn" if is_selected else "chat-container"
    st.markdown(f"<div class='{container_class}'>", unsafe_allow_html=True)
    
    # User message first (left)
    st.markdown("""
        <div class='chat-name'>User</div>
        <div class='chat-bubble coach-bubble'>
            {message}
        </div>
    """.format(message=turn.coach_message.replace("\n", "<br>")), unsafe_allow_html=True)
    
    # Coach message second (right)
    st.markdown("""
        <div class='chat-name user-name'>Coach</div>
        <div class='chat-bubble user-bubble'>
            {message}
        </div>
    """.format(message=turn.user_message.replace("\n", "<br>")), unsafe_allow_html=True)
    
    # Show belief updates if any
    if turn.belief_updates:
        st.markdown("<div style='margin-top: 12px;'>", unsafe_allow_html=True)
        render_belief_diff(turn.belief_updates["old"], turn.belief_updates["new"])
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Show metrics summary if available
    metrics_summary = TurnMetricsSummary(metrics=getattr(turn, 'metrics', None))
    metrics_summary.render_indicator()
    
    st.markdown("</div>", unsafe_allow_html=True)

def render_conversation_sidebar(
    turns: List[Turn],
    current_turn_id: Optional[str],
    on_turn_selected: Callable[[str], None]
):
    """Render the conversation sidebar with all turns"""
    st.sidebar.title("Conversation")
    
    for turn in turns:
        turn_container = st.sidebar.container()
        with turn_container:
            render_conversation_turn(
                turn=turn,
                is_selected=turn.id == current_turn_id
            )
            
            if st.button("Select", key=f"select_{turn.id}"):
                on_turn_selected(turn.id) 