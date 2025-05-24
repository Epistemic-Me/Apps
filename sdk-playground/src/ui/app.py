import streamlit as st
# Page config must be the first Streamlit command
st.set_page_config(layout="wide", page_title="Epistemic SDK Playground")

st.title("Epistemic SDK Playground")

st.markdown("""
Welcome to the Epistemic SDK Playground!

This tool lets you explore and evaluate agent systems, datasets, and conversational flows.

**Pages available:**
- Philosopher's Workbench: Explore philosophical tools and reasoning.
- Agent System Definition: Define and configure agent systems.
- Agent Conversational Dataset: View and manage agent conversations.
- Agent Evaluation: Evaluate agent performance and metrics.

Select a page from the sidebar to get started.
""") 