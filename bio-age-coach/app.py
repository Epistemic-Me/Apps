"""Streamlit application for the Bio Age Coach."""

import os
import asyncio
import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from dotenv import load_dotenv
from bio_age_coach.chatbot.coach import BioAgeCoach
from bio_age_coach.mcp.client import MultiServerMCPClient
from bio_age_coach.mcp.router import QueryRouter
from bio_age_coach.mcp.health_server import HealthServer
from bio_age_coach.mcp.research_server import ResearchServer
from bio_age_coach.mcp.tools_server import ToolsServer
from bio_age_coach.mcp.bio_age_score_server import BioAgeScoreServer

# Load environment variables
load_dotenv()

async def init_mcp_servers():
    """Initialize MCP servers with API key and health data path."""
    api_key = os.getenv("OPENAI_API_KEY", "default_key")
    health_data_path = "data/health"
    papers_dir = "data/papers"

    # Initialize servers
    health_server = HealthServer(api_key, health_data_path)
    research_server = ResearchServer(api_key, papers_dir)
    tools_server = ToolsServer(api_key)
    bio_age_score_server = BioAgeScoreServer(api_key)

    # Initialize test users and data
    test_users = [
        {"id": "test_user_1", "username": "Test User 1"},
        {"id": "test_user_2", "username": "Test User 2"}
    ]
    
    # Load test health data from the test script
    from test_bio_age_score_server import process_workout_data
    data_dir = os.path.join(os.path.dirname(__file__), 'data', 'test_health_data')
    daily_metrics = process_workout_data(data_dir)
    
    # Initialize health data for test users
    test_data = {
        "health_data": daily_metrics,
        "bio_age_tests": {
            "push_ups": 25,
            "grip_strength": 85,
            "one_leg_stand": 45
        },
        "capabilities": {
            "vo2_max": 42.5,
            "cognitive_speed": 220,
            "recovery_rate": 25
        },
        "biomarkers": {
            "hba1c": 5.2,
            "fasting_glucose": 88,
            "crp": 0.6
        },
        "measurements": {
            "body_fat": 18.5,
            "waist_to_height": 0.43,
            "muscle_mass": 42.0
        },
        "lab_results": {
            "telomere_length": 8.2,
            "dna_methylation": 35,
            "glycan_age": 32
        }
    }
    
    # Initialize servers with test data
    await health_server.initialize_data({"users": test_users})
    
    # Update each user's data
    for user in test_users:
        user_data = {"username": user["username"]}
        user_data.update(test_data)
        await health_server.update_user_data(user["id"], user_data)
    
    # Initialize bio age score server
    await bio_age_score_server.initialize_data(test_data)

    # Create MCP client and query router
    mcp_client = MultiServerMCPClient(
        health_server=health_server,
        research_server=research_server,
        tools_server=tools_server,
        bio_age_score_server=bio_age_score_server
    )
    query_router = QueryRouter(
        health_server=health_server,
        research_server=research_server,
        tools_server=tools_server,
        bio_age_score_server=bio_age_score_server
    )

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

async def load_user_data(user_id: str, mcp_client: MultiServerMCPClient) -> bool:
    """Load user data from the HealthServer."""
    try:
        # Get user data from HealthServer
        response = await mcp_client.send_request(
            "health",
            {
                "type": "user_data",
                "user_id": user_id,
                "api_key": os.getenv("OPENAI_API_KEY")
            }
        )
        
        if "error" in response:
            return False
            
        # Update coach's user data
        st.session_state.coach.update_user_data(response)
        
        # Create welcome message based on data completeness
        completeness = st.session_state.coach.calculate_overall_completeness()
        user_info = await mcp_client.send_request(
            "health",
            {
                "type": "users",
                "api_key": os.getenv("OPENAI_API_KEY")
            }
        )
        username = next((user["username"] for user in user_info["users"] if user["id"] == user_id), "User")
        
        welcome_message = f"👋 Hello {username}! I've loaded your health data profile, which is currently {int(completeness*100)}% complete."
        
        if completeness < 0.2:
            welcome_message += "\n\nYou're just getting started! Let's collect some fundamental measurements to better understand your biological age factors."
        elif completeness < 0.5:
            welcome_message += "\n\nYou have a good foundation of health data. Let's fill in some key metrics to get a clearer picture of your biological age."
        elif completeness < 0.8:
            welcome_message += "\n\nYour health profile is quite comprehensive. We can now provide a meaningful assessment of your biological age factors."
        else:
            welcome_message += "\n\nYou have an excellent health profile with comprehensive data. This allows for a detailed analysis of your biological age and optimization opportunities."
        
        # Add the welcome message to the chat
        st.session_state.messages = []
        st.session_state.messages.append({"role": "assistant", "content": welcome_message})
        
        return True
    except Exception as e:
        print(f"Error loading user data: {e}")
        return False

async def get_daily_health_summary(user_id: str, mcp_client: MultiServerMCPClient) -> dict:
    """Get a summary of the user's daily health metrics from the HealthServer."""
    try:
        response = await mcp_client.send_request(
            "health",
            {
                "type": "trends",
                "user_id": user_id,
                "api_key": os.getenv("OPENAI_API_KEY")
            }
        )
        
        if "error" in response:
            return None
            
        daily_data = response["trends"]
        if not daily_data:
            return None
            
        # Calculate averages
        avg_calories = sum(d['active_calories'] for d in daily_data) / len(daily_data)
        avg_steps = sum(d['steps'] for d in daily_data) / len(daily_data)
        avg_sleep = sum(d['sleep_hours'] for d in daily_data) / len(daily_data)
        avg_score = sum(d['daily_score'] for d in daily_data) / len(daily_data)
        
        return {
            "avg_calories": round(avg_calories, 1),
            "avg_steps": round(avg_steps, 0),
            "avg_sleep": round(avg_sleep, 1),
            "avg_score": round(avg_score, 1),
            "days": len(daily_data)
        }
    except Exception as e:
        print(f"Error getting daily health summary: {e}")
        return None

async def main():
    """Main function to run the Streamlit app."""
    st.title("Bio Age Coach")
    st.write("Your AI coach for optimizing biological age and longevity.")

    # Initialize session state
    initialize_session_state()

    # Initialize MCP servers if not already done
    if not st.session_state.mcp_client or not st.session_state.query_router:
        mcp_client, query_router = await init_mcp_servers()
        st.session_state.mcp_client = mcp_client
        st.session_state.query_router = query_router
        st.session_state.coach = BioAgeCoach(mcp_client, query_router)

    # User selection in sidebar
    with st.sidebar:
        st.header("User Selection")
        
        # Debug print to see what's in the response
        users_response = await st.session_state.mcp_client.send_request(
            "health",
            {
                "type": "users",
                "api_key": os.getenv("OPENAI_API_KEY")
            }
        )
        st.write("Debug - Users Response:", users_response)  # Debug print
        
        if "users" in users_response and users_response["users"]:
            user_options = {f"{user['username']} (ID: {user['id']})": user['id'] 
                          for user in users_response["users"]}
            
            # Debug print to see available options
            st.write("Debug - Available Users:", list(user_options.keys()))  # Debug print
            
            # Ensure there's a default option
            if not user_options:
                st.error("No users available")
            else:
                selected_user = st.selectbox(
                    "Select User",
                    options=list(user_options.keys()),
                    key="user_selector"
                )
                
                if selected_user:  # Only proceed if a user is selected
                    user_id = user_options[selected_user]
                    
                    if user_id != st.session_state.selected_user_id:
                        st.session_state.selected_user_id = user_id
                        if await load_user_data(user_id, st.session_state.mcp_client):
                            st.session_state.user_data_loaded = True
                            st.rerun()
        else:
            st.error("No users found in the system")

    # Main content area
    if st.session_state.user_data_loaded:
        # Display health summary if available
        if st.session_state.selected_user_id:
            summary = await get_daily_health_summary(
                st.session_state.selected_user_id,
                st.session_state.mcp_client
            )
            if summary:
                st.header(f"Daily Health Metrics (Last {summary['days']} days)")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Avg. Active Calories", f"{summary['avg_calories']}")
                with col2:
                    st.metric("Avg. Steps", f"{int(summary['avg_steps']):,}")
                with col3:
                    st.metric("Avg. Sleep (hrs)", f"{summary['avg_sleep']}")
                with col4:
                    st.metric("Avg. Health Score", f"{summary['avg_score']}/100")

        # Chat interface
        st.header("Chat with Your Coach")
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                if isinstance(message.get("content"), dict) and "visualization" in message["content"]:
                    # Display visualization data
                    viz_data = message["content"]["visualization"]
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
                            if "insights" in message["content"]:
                                st.markdown("### Key Insights")
                                for insight in message["content"]["insights"]:
                                    st.markdown(f"- {insight}")
                        except Exception as e:
                            st.error(f"Error displaying visualization: {str(e)}")
                else:
                    st.markdown(message["content"])

        if prompt := st.chat_input("Type your message here..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = await st.session_state.coach.process_message(prompt)
                    if isinstance(response, dict) and "visualization" in response:
                        st.session_state.messages.append({"role": "assistant", "content": response})
                        # Display visualization immediately
                        try:
                            viz_data = response["visualization"]
                            if viz_data and "dates" in viz_data and "scores" in viz_data:
                                fig = plt.figure(figsize=(10, 6))
                                
                                # Plot scores
                                plt.plot(range(len(viz_data["dates"])), viz_data["scores"], 
                                       label="Bio Age Score", color='blue', linewidth=2)
                                
                                # Plot reference ranges
                                ref_ranges = viz_data["reference_ranges"]
                                plt.fill_between(range(len(viz_data["dates"])), 
                                               ref_ranges["optimal_min"],
                                               ref_ranges["optimal_max"],
                                               alpha=0.2, color='green', label='Optimal Range')
                                plt.fill_between(range(len(viz_data["dates"])),
                                               ref_ranges["good_min"],
                                               ref_ranges["good_max"],
                                               alpha=0.2, color='yellow', label='Good Range')
                                
                                # Customize plot
                                plt.xticks(range(len(viz_data["dates"])), viz_data["dates"], 
                                         rotation=45, ha='right')
                                plt.xlabel("Date")
                                plt.ylabel("Score")
                                plt.title("Bio Age Score Trends")
                                plt.legend()
                                plt.grid(True, alpha=0.3)
                                plt.tight_layout()
                                
                                # Display plot
                                st.pyplot(fig)
                                plt.close()
                                
                                # Display insights
                                if "insights" in response:
                                    st.markdown("### Key Insights")
                                    for insight in response["insights"]:
                                        st.markdown(f"- {insight}")
                            else:
                                st.error("Invalid visualization data format")
                        except Exception as e:
                            st.error(f"Error displaying visualization: {str(e)}")
                    else:
                        st.markdown(response)
                        st.session_state.messages.append({"role": "assistant", "content": response})
    else:
        st.info("Please select a user to begin.")

if __name__ == "__main__":
    asyncio.run(main()) 