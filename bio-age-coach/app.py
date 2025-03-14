"""Streamlit application for the Bio Age Coach."""

import os
import asyncio
import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from dotenv import load_dotenv
from bio_age_coach.chatbot.coach import BioAgeCoach
from bio_age_coach.mcp.utils.client import MultiServerMCPClient
from bio_age_coach.mcp.core.router import QueryRouter
from bio_age_coach.mcp.servers.health_server import HealthServer
from bio_age_coach.mcp.servers.research_server import ResearchServer
from bio_age_coach.mcp.servers.tools_server import ToolsServer
from bio_age_coach.mcp.servers.bio_age_score_server import BioAgeScoreServer
from bio_age_coach.mcp.core.module_registry import ModuleRegistry
import json

# Load environment variables
load_dotenv()

async def init_mcp_servers():
    """Initialize MCP servers and conversation modules."""
    api_key = os.getenv("OPENAI_API_KEY", "default_key")
    papers_dir = "data/papers"
    test_data_path = os.path.join(os.path.dirname(__file__), "data/test_health_data")

    # Initialize test users
    test_users = [
        {"id": "test_user_1", "username": "Test User 1"}
    ]

    # Create MCP client first
    mcp_client = MultiServerMCPClient()

    # Initialize servers
    health_server = HealthServer(api_key)
    # Initialize with test data path - HealthServer will load all CSV files
    await health_server.initialize_data({
        "test_data_path": test_data_path,
        "users": test_users,
        "process_test_data": True  # Tell HealthServer to process all CSV files
    })

    research_server = ResearchServer(api_key, papers_dir)
    tools_server = ToolsServer(api_key)
    bio_age_score_server = BioAgeScoreServer(api_key)

    # Register servers with MCP client
    mcp_client.register_server("health", health_server)
    mcp_client.register_server("research", research_server)
    mcp_client.register_server("tools", tools_server)
    mcp_client.register_server("bio_age_score", bio_age_score_server)

    # Initialize conversation module registry with mcp_client
    module_registry = ModuleRegistry(mcp_client)

    # Update each user's data and initialize bio age score server
    for user in test_users:
        # Get metrics data from health server
        metrics_response = await mcp_client.send_request(
            "health",
            {
                "type": "metrics",
                "timeframe": "30D"
            }
        )
        
        if "error" not in metrics_response:
            # Initialize bio age score server with the health data
            await bio_age_score_server.initialize_data({
                "user_id": user["id"],
                "health_data": metrics_response.get("metrics", [])
            })

    # Create query router with mcp_client and module_registry
    query_router = QueryRouter(mcp_client=mcp_client, module_registry=module_registry)

    return mcp_client, query_router

def initialize_session_state():
    """Initialize session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "coach" not in st.session_state:
        st.session_state.coach = None
    if "mcp_client" not in st.session_state:
        st.session_state.mcp_client = None
    if "query_router" not in st.session_state:
        st.session_state.query_router = None
    if "selected_user_id" not in st.session_state:
        st.session_state.selected_user_id = None
    if "user_data_loaded" not in st.session_state:
        st.session_state.user_data_loaded = False
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []
    if "current_topic" not in st.session_state:
        st.session_state.current_topic = None

async def load_user_data(user_id: str, mcp_client: MultiServerMCPClient) -> bool:
    """Load user data from HealthServer."""
    try:
        # Get metrics data from health server
        metrics_response = await mcp_client.send_request(
            "health",
            {
                "type": "metrics",
                "timeframe": "30D"
            }
        )

        if "error" in metrics_response:
            st.error(f"Error loading metrics data: {metrics_response['error']}")
            return False

        # Update session state with user data
        st.session_state.user_data = {
            "metrics": metrics_response.get("metrics", []),
            "workouts": metrics_response.get("workouts", [])
        }
        st.session_state.user_data_loaded = True

        # Update bio age score server with the metrics data
        await mcp_client.send_request(
            "bio_age_score",
            {
                "type": "initialize",
                "data": {
                    "user_id": user_id,
                    "health_data": metrics_response.get("metrics", [])
                }
            }
        )

        # Update the coach's user data
        if st.session_state.coach:
            st.session_state.coach.update_user_data({
                "health_data": metrics_response.get("metrics", []),
                "workouts": metrics_response.get("workouts", [])
            })

        return True

    except Exception as e:
        st.error(f"Error loading user data: {str(e)}")
        return False

async def get_daily_health_summary(user_id: str, mcp_client: MultiServerMCPClient) -> dict:
    """Get a summary of daily health metrics."""
    try:
        # Get metrics data
        response = await mcp_client.send_request(
            "health",
            {
                "type": "metrics",
                "timeframe": "30D",
                "api_key": os.getenv("OPENAI_API_KEY")
            }
        )
        
        if "error" in response:
            return None
            
        metrics = response.get("metrics", [])
        if not metrics:
            return None
            
        # Get the most recent date's data
        latest_metrics = metrics[-1]  # Assuming metrics are sorted by date
        
        return {
            "avg_calories": latest_metrics.get("active_calories", 0),
            "avg_steps": latest_metrics.get("steps", 0),
            "avg_sleep": latest_metrics.get("sleep_hours", 0),
            "avg_score": latest_metrics.get("health_score", 0),
            "days": 1  # For now, just showing the most recent day
        }
    except Exception as e:
        st.error(f"Error getting daily health summary: {str(e)}")
        return None

async def main():
    """Main function for the Streamlit app."""
    st.title("Bio Age Coach")
    
    # Initialize session state
    initialize_session_state()
    
    # Initialize MCP servers if not already done
    if not st.session_state.mcp_client or not st.session_state.query_router:
        mcp_client, query_router = await init_mcp_servers()
        st.session_state.mcp_client = mcp_client
        st.session_state.query_router = query_router
        st.session_state.coach = await BioAgeCoach.create(mcp_client, query_router)
    
    # User selection in sidebar
    with st.sidebar:
        st.header("User Selection")
        
        # Simplified user selection with test user
        user_options = {
            "Test User 1": "test_user_1"
        }
        
        selected_user = st.selectbox(
            "Select User",
            options=list(user_options.keys()),
            key="user_selector"
        )
        
        selected_user_id = user_options[selected_user]
        
        # Load user data if user changed
        if st.session_state.selected_user_id != selected_user_id:
            st.session_state.selected_user_id = selected_user_id
            st.session_state.user_data_loaded = False
            st.session_state.messages = []
            
        # Load user data if not loaded
        if not st.session_state.user_data_loaded:
            with st.spinner("Loading user data..."):
                if await load_user_data(selected_user_id, st.session_state.mcp_client):
                    st.success("Data loaded successfully!")
                    
                    # Initialize the coach with the loaded data
                    if "user_data" in st.session_state:
                        st.session_state.coach.update_user_data(st.session_state.user_data)
                        
                        # Add welcome message
                        welcome_message = f"👋 Hello! I've loaded your health data. Let me help you understand and optimize your biological age."
                        st.session_state.messages.append({"role": "assistant", "content": welcome_message})
    
    # Main content area
    if st.session_state.user_data_loaded:
        # Display health summary
        if st.session_state.selected_user_id:
            summary = await get_daily_health_summary(
                st.session_state.selected_user_id,
                st.session_state.mcp_client
            )
            if summary:
                st.header("Current Health Metrics")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Active Calories", f"{summary['avg_calories']}")
                with col2:
                    st.metric("Steps", f"{int(summary['avg_steps']):,}")
                with col3:
                    st.metric("Sleep (hrs)", f"{summary['avg_sleep']}")
                with col4:
                    st.metric("Health Score", f"{summary['avg_score']}/100")
        
        # Chat interface
        st.header("Chat with Your Coach")
        
        # Display messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                if isinstance(message.get("content"), dict):
                    content = message["content"]
                    if "error" in content:
                        st.error(content["error"])
                    elif "visualization" in content:
                        # Display visualization data
                        viz_data = content["visualization"]
                        if viz_data:
                            try:
                                # Create figure from the visualization data
                                fig = plt.figure(figsize=(10, 6))
                                plt.plot(viz_data["dates"], viz_data["scores"], label="Bio Age Score")
                                plt.fill_between(viz_data["dates"], 
                                              viz_data["reference_ranges"]["optimal_min"],
                                              viz_data["reference_ranges"]["optimal_max"],
                                              alpha=0.2, color='green', label='Optimal Range')
                                plt.fill_between(viz_data["dates"],
                                              viz_data["reference_ranges"]["good_min"],
                                              viz_data["reference_ranges"]["good_max"],
                                              alpha=0.2, color='yellow', label='Good Range')
                                plt.xlabel("Date")
                                plt.ylabel("Score")
                                plt.title("Bio Age Score Trends")
                                plt.legend()
                                st.pyplot(fig)
                                plt.close()
                                
                                # Display insights
                                if "insights" in content:
                                    st.markdown("### Key Insights")
                                    for insight in content["insights"]:
                                        st.markdown(f"- {insight}")
                            except Exception as e:
                                st.error(f"Error displaying visualization: {str(e)}")
                    elif "response" in content:
                        st.markdown(content["response"])
                        if "insights" in content:
                            st.markdown("### Key Insights")
                            for insight in content["insights"]:
                                st.markdown(f"- {insight}")
                else:
                    st.markdown(message["content"])
        
        # User input
        if prompt := st.chat_input("Type your message here..."):
            # Add user message
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Get assistant response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = await st.session_state.coach.process_message(prompt)
                    if isinstance(response, dict):
                        st.session_state.messages.append({"role": "assistant", "content": response})
                        # Handle different response types
                        if "error" in response:
                            st.error(response["error"])
                        elif "visualization" in response:
                            try:
                                viz_data = response["visualization"]
                                if viz_data and "dates" in viz_data and "scores" in viz_data:
                                    fig = plt.figure(figsize=(10, 6))
                                    plt.plot(range(len(viz_data["dates"])), viz_data["scores"], 
                                           label="Bio Age Score", color='blue', linewidth=2)
                                    plt.fill_between(range(len(viz_data["dates"])), 
                                                   viz_data["reference_ranges"]["optimal_min"],
                                                   viz_data["reference_ranges"]["optimal_max"],
                                                   alpha=0.2, color='green', label='Optimal Range')
                                    plt.fill_between(range(len(viz_data["dates"])),
                                                   viz_data["reference_ranges"]["good_min"],
                                                   viz_data["reference_ranges"]["good_max"],
                                                   alpha=0.2, color='yellow', label='Good Range')
                                    plt.xticks(range(len(viz_data["dates"])), viz_data["dates"], 
                                             rotation=45, ha='right')
                                    plt.xlabel("Date")
                                    plt.ylabel("Score")
                                    plt.title("Bio Age Score Trends")
                                    plt.legend()
                                    plt.grid(True, alpha=0.3)
                                    plt.tight_layout()
                                    st.pyplot(fig)
                                    plt.close()
                                    
                                    if "insights" in response:
                                        st.markdown("### Key Insights")
                                        for insight in response["insights"]:
                                            st.markdown(f"- {insight}")
                            except Exception as e:
                                st.error(f"Error displaying visualization: {str(e)}")
                        elif "response" in response:
                            st.markdown(response["response"])
                            if "insights" in response:
                                st.markdown("### Key Insights")
                                for insight in response["insights"]:
                                    st.markdown(f"- {insight}")
                    else:
                        st.markdown(response)
                        st.session_state.messages.append({"role": "assistant", "content": response})
            
            # Force a rerun to update the display
            st.rerun()
    else:
        st.info("Please select a user to begin.")

if __name__ == "__main__":
    asyncio.run(main()) 