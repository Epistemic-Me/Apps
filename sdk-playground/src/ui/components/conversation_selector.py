import streamlit as st
from typing import List, Optional
from deepeval.dataset import EvaluationDataset
from deepeval.test_case import ConversationalTestCase

class ConversationSelector:
    def __init__(self):
        """Initialize the conversation selector"""
        if 'datasets' not in st.session_state:
            st.session_state.datasets = []
        if 'current_dataset_index' not in st.session_state:
            st.session_state.current_dataset_index = 0
        if 'current_conversation_index' not in st.session_state:
            st.session_state.current_conversation_index = 0
        if 'current_router_intent' not in st.session_state:
            st.session_state.current_router_intent = "Lower BioAge Score"

    def handle_dataset_selection(self):
        """Handle selection of a dataset"""
        if not st.session_state.datasets:
            return None
            
        dataset_names = [dataset.name for dataset in st.session_state.datasets]
        selected_name = st.selectbox(
            "Select User Cohort",
            dataset_names,
            index=st.session_state.current_dataset_index
        )
        
        # Update dataset index if changed
        new_index = dataset_names.index(selected_name)
        if new_index != st.session_state.current_dataset_index:
            st.session_state.current_dataset_index = new_index
            st.session_state.current_conversation_index = 0  # Reset conversation selection
            st.rerun()

    def handle_router_intent_selection(self):
        """Handle selection of router intent"""
        router_intents = [
            "Lower BioAge Score",
            "Query Health Analysis",
            "Research Health",
            "View Health Data as Visualization"
        ]
        
        selected_intent = st.selectbox(
            "Select AI Coach Router Intent",
            router_intents,
            index=router_intents.index(st.session_state.current_router_intent)
        )
        
        if selected_intent != st.session_state.current_router_intent:
            st.session_state.current_router_intent = selected_intent
            st.session_state.current_conversation_index = 0  # Reset conversation selection
            st.rerun()

    def get_filtered_conversations(self):
        """Get conversations filtered by current router intent"""
        if not st.session_state.datasets:
            return []
            
        # Handle invalid dataset index
        if st.session_state.current_dataset_index >= len(st.session_state.datasets):
            st.session_state.current_dataset_index = 0
        
        current_dataset = st.session_state.datasets[st.session_state.current_dataset_index]
        filtered_conversations = []
        
        for test_case in current_dataset.test_cases:
            # Extract router intent from context
            if not test_case.turns:
                continue
                
            # Get context from first turn
            context = test_case.turns[0].context
            if not context:
                continue
                
            # Find router intent in context strings
            context_strings = context if isinstance(context, list) else [context]
            router_intent_line = next((line for line in context_strings if isinstance(line, str) and line.startswith('Router Intent:')), None)
            if not router_intent_line:
                continue
                
            # Extract intent from the line
            intent = router_intent_line.split(': ')[1]
            if intent == st.session_state.current_router_intent:
                filtered_conversations.append(test_case)
        
        return filtered_conversations

    def handle_conversation_selection(self):
        """Handle selection of a conversation within the current dataset"""
        filtered_conversations = self.get_filtered_conversations()
        if not filtered_conversations:
            st.info(f"No conversations available for intent: {st.session_state.current_router_intent}")
            return None
            
        num_conversations = len(filtered_conversations)
        
        selected_index = st.selectbox(
            "Select Conversation",
            range(num_conversations),
            index=min(st.session_state.current_conversation_index, num_conversations - 1),
            format_func=lambda x: f"Conversation {x + 1}"
        )
        
        # Update conversation index if changed
        if selected_index != st.session_state.current_conversation_index:
            st.session_state.current_conversation_index = selected_index
            st.rerun()

    def get_current_conversation(self) -> Optional[ConversationalTestCase]:
        """Get the currently selected conversation"""
        filtered_conversations = self.get_filtered_conversations()
        if not filtered_conversations:
            return None
            
        if st.session_state.current_conversation_index >= len(filtered_conversations):
            st.session_state.current_conversation_index = 0
            
        return filtered_conversations[st.session_state.current_conversation_index]

    def render(self):
        """Render the dataset and conversation selectors"""
        with st.sidebar:
            st.subheader("User Selection")
            self.handle_dataset_selection()
            
            st.subheader("Router Intent")
            self.handle_router_intent_selection()
            
            st.subheader("Conversation Selection")
            self.handle_conversation_selection() 