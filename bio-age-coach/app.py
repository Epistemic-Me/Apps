"""Streamlit application for the Bio Age Coach."""

import os
import asyncio
import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from dotenv import load_dotenv
from bio_age_coach.chatbot.coach import BioAgeCoach
from bio_age_coach.mcp.utils.client import MultiServerMCPClient
from bio_age_coach.mcp.core.module_registry import ModuleRegistry
from bio_age_coach.mcp.servers.health_server import HealthServer
from bio_age_coach.mcp.servers.research_server import ResearchServer
from bio_age_coach.mcp.servers.tools_server import ToolsServer
from bio_age_coach.mcp.servers.bio_age_score_server import BioAgeScoreServer
from bio_age_coach.router.router_adapter import RouterAdapter
from bio_age_coach.router.semantic_router import SemanticRouter
from bio_age_coach.agents.factory import create_agents
import json
import seaborn as sns
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap

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
    mcp_client = MultiServerMCPClient(api_key=api_key)

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
    await mcp_client.add_server("health", health_server)
    await mcp_client.add_server("research", research_server)
    await mcp_client.add_server("tools", tools_server)
    await mcp_client.add_server("bio_age_score", bio_age_score_server)

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

    # Create agents for the semantic router
    agents = create_agents(api_key, mcp_client)
    
    # Create semantic router with agents
    semantic_router = SemanticRouter(api_key=api_key, agents=agents)
    
    # Create router adapter with semantic router
    router_adapter = RouterAdapter(
        semantic_router=semantic_router,
        mcp_client=mcp_client,
        module_registry=module_registry
    )

    return mcp_client, router_adapter

def initialize_session_state():
    """Initialize session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "coach" not in st.session_state:
        st.session_state.coach = None
    if "mcp_client" not in st.session_state:
        st.session_state.mcp_client = None
    if "router_adapter" not in st.session_state:
        st.session_state.router_adapter = None
    if "selected_user_id" not in st.session_state:
        st.session_state.selected_user_id = None
    if "user_data_loaded" not in st.session_state:
        st.session_state.user_data_loaded = False
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []
    if "current_topic" not in st.session_state:
        st.session_state.current_topic = None
    if "active_context" not in st.session_state:
        st.session_state.active_context = {"active_topic": None, "observation_contexts": {}}

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

def create_visualization(viz_data, viz_type="line"):
    """Create a visualization based on the data and type.
    
    Args:
        viz_data: The visualization data
        viz_type: The type of visualization to create (line, bar, radar, heatmap)
        
    Returns:
        matplotlib.figure.Figure: The created figure
    """
    if not viz_data:
        return None
        
    # Set the style for all plots
    sns.set_style("whitegrid")
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = ['Arial', 'Helvetica', 'DejaVu Sans']
    plt.rcParams['axes.edgecolor'] = '#DDDDDD'
    plt.rcParams['axes.linewidth'] = 0.8
    plt.rcParams['xtick.color'] = '#555555'
    plt.rcParams['ytick.color'] = '#555555'
    
    # Create a new figure with a unique identifier
    fig = plt.figure(figsize=(12, 6))
    
    try:
        # Create figure based on visualization type
        if viz_type == "line" and "dates" in viz_data and "scores" in viz_data:
            # Line chart for time series data
            
            # Plot the main line with a gradient color
            cm = LinearSegmentedColormap.from_list('bio_age', ['#4CAF50', '#2196F3', '#9C27B0'], N=256)
            points = np.array([viz_data["dates"], viz_data["scores"]]).T.reshape(-1, 1, 2)
            segments = np.concatenate([points[:-1], points[1:]], axis=1)
            
            # Create a line collection
            from matplotlib.collections import LineCollection
            lc = LineCollection(segments, cmap=cm, linewidth=3)
            lc.set_array(np.linspace(0, 1, len(viz_data["scores"])))
            
            ax = plt.gca()
            ax.add_collection(lc)
            
            # Add markers for each data point
            plt.scatter(viz_data["dates"], viz_data["scores"], c=np.linspace(0, 1, len(viz_data["scores"])), 
                       cmap=cm, s=80, zorder=3, edgecolor='white', linewidth=1.5)
            
            # Add reference ranges
            if "reference_ranges" in viz_data:
                plt.fill_between(viz_data["dates"], 
                              viz_data["reference_ranges"]["optimal_min"],
                              viz_data["reference_ranges"]["optimal_max"],
                              alpha=0.15, color='green', label='Optimal Range')
                plt.fill_between(viz_data["dates"],
                              viz_data["reference_ranges"]["good_min"],
                              viz_data["reference_ranges"]["good_max"],
                              alpha=0.1, color='orange', label='Good Range')
            
            # Add trend line
            if len(viz_data["scores"]) > 2:
                z = np.polyfit(range(len(viz_data["dates"])), viz_data["scores"], 1)
                p = np.poly1d(z)
                plt.plot(viz_data["dates"], p(range(len(viz_data["dates"]))), 
                       "r--", alpha=0.7, linewidth=1.5, label="Trend")
            
            # Set labels and title
            plt.xlabel("Date", fontsize=12, color="#333333")
            plt.ylabel("Score", fontsize=12, color="#333333")
            plt.title("Bio Age Score Trends", fontsize=16, color="#333333", fontweight='bold')
            
            # Customize x-axis
            plt.xticks(rotation=45, ha='right')
            
            # Add grid
            plt.grid(True, linestyle='--', alpha=0.7)
            
            # Add legend
            plt.legend(loc='upper left', frameon=True, framealpha=0.9)
            
        elif viz_type == "bar" and "categories" in viz_data and "values" in viz_data:
            # Bar chart for categorical data
            
            # Create a custom colormap
            colors = sns.color_palette("viridis", len(viz_data["categories"]))
            
            # Create the bar chart
            bars = plt.bar(viz_data["categories"], viz_data["values"], color=colors)
            
            # Add value labels on top of bars
            for bar in bars:
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                       f'{height:.1f}', ha='center', va='bottom', fontsize=10)
            
            # Set labels and title
            plt.xlabel(viz_data.get("x_label", "Categories"), fontsize=12, color="#333333")
            plt.ylabel(viz_data.get("y_label", "Values"), fontsize=12, color="#333333")
            plt.title(viz_data.get("title", "Bar Chart"), fontsize=16, color="#333333", fontweight='bold')
            
            # Add reference line if provided
            if "reference_line" in viz_data:
                plt.axhline(y=viz_data["reference_line"], color='r', linestyle='--', 
                          alpha=0.7, label=viz_data.get("reference_label", "Reference"))
                plt.legend()
            
        elif viz_type == "radar" and "categories" in viz_data and "values" in viz_data:
            # Radar chart for multi-dimensional data
            
            # Create radar chart
            categories = viz_data["categories"]
            values = viz_data["values"]
            
            # Close the loop for the radar chart
            categories = np.concatenate((categories, [categories[0]]))
            values = np.concatenate((values, [values[0]]))
            
            # Calculate angles for each category
            angles = np.linspace(0, 2*np.pi, len(categories), endpoint=False).tolist()
            angles += angles[:1]  # Close the loop
            
            # Create subplot with polar projection
            ax = fig.add_subplot(111, polar=True)
            
            # Plot data
            ax.plot(angles, values, 'o-', linewidth=2, label=viz_data.get("label", "Data"))
            ax.fill(angles, values, alpha=0.25)
            
            # Set category labels
            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(categories[:-1])
            
            # Set y-axis limits if provided
            if "y_limits" in viz_data:
                ax.set_ylim(viz_data["y_limits"])
            
            # Add title
            plt.title(viz_data.get("title", "Radar Chart"), fontsize=16, color="#333333", fontweight='bold')
            
            # Add reference values if provided
            if "reference_values" in viz_data:
                ref_values = viz_data["reference_values"]
                ref_values = np.concatenate((ref_values, [ref_values[0]]))  # Close the loop
                ax.plot(angles, ref_values, 'o-', linewidth=2, alpha=0.7, 
                      label=viz_data.get("reference_label", "Reference"))
                ax.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1))
            
        elif viz_type == "heatmap" and "data_matrix" in viz_data:
            # Heatmap for matrix data
            
            # Create heatmap
            sns.heatmap(viz_data["data_matrix"], 
                      annot=viz_data.get("show_values", True),
                      cmap=viz_data.get("colormap", "viridis"),
                      linewidths=0.5,
                      xticklabels=viz_data.get("x_labels", True),
                      yticklabels=viz_data.get("y_labels", True),
                      cbar_kws={'label': viz_data.get("colorbar_label", "Value")})
            
            # Set title
            plt.title(viz_data.get("title", "Heatmap"), fontsize=16, color="#333333", fontweight='bold')
            
        else:
            # Default to a simple line chart if the data doesn't match any specific type
            
            # Try to plot whatever data is available
            if "x" in viz_data and "y" in viz_data:
                plt.plot(viz_data["x"], viz_data["y"])
                plt.xlabel(viz_data.get("x_label", "X"))
                plt.ylabel(viz_data.get("y_label", "Y"))
                plt.title(viz_data.get("title", "Chart"))
            else:
                # Create an empty chart with a message
                plt.text(0.5, 0.5, "No visualization data available", 
                       horizontalalignment='center', verticalalignment='center',
                       transform=plt.gca().transAxes, fontsize=14)
                plt.axis('off')
        
        # Adjust layout for all plot types
        plt.tight_layout()
        
        return fig
    except Exception as e:
        print(f"Error creating visualization: {e}")
        # Create a simple error message plot
        plt.clf()  # Clear the figure
        plt.text(0.5, 0.5, f"Error creating visualization: {str(e)}", 
               horizontalalignment='center', verticalalignment='center',
               transform=plt.gca().transAxes, fontsize=12, color='red')
        plt.axis('off')
        return fig

def update_session_context():
    """Update the session state with the latest observation context from the coach."""
    if "coach" in st.session_state and st.session_state.coach:
        # Get the active context from the coach
        active_context = st.session_state.coach.get_active_context()
        
        # Determine the active topic based on the highest relevancy observation context
        observation_contexts = active_context.get('observation_contexts', {})
        if observation_contexts:
            # Find the observation context with the highest relevancy score
            highest_relevancy = 0.0
            highest_context = None
            for agent_name, context in observation_contexts.items():
                relevancy = context.get('relevancy_score', 0.0)
                if relevancy > highest_relevancy:
                    highest_relevancy = relevancy
                    highest_context = context
            
            # Set the active topic based on the highest relevancy context
            if highest_context and highest_relevancy >= 0.4:  # Only set if relevancy is significant
                data_type = highest_context.get('data_type', 'unknown')
                active_context['active_topic'] = data_type.capitalize()
        
        # Update the session state with the modified active context
        st.session_state.active_context = active_context
        print(f"Updated session context: {st.session_state.active_context}")

async def main():
    """Main function for the Streamlit app."""
    st.title("Bio Age Coach")
    
    # Initialize session state
    initialize_session_state()
    
    # Initialize MCP servers if not already done
    if not st.session_state.mcp_client or not st.session_state.router_adapter:
        mcp_client, router_adapter = await init_mcp_servers()
        st.session_state.mcp_client = mcp_client
        st.session_state.router_adapter = router_adapter
        st.session_state.coach = await BioAgeCoach.create(mcp_client, router_adapter)
    
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
        
        # File upload section in sidebar
        st.header("Upload Health Data")
        uploaded_file = st.file_uploader("Upload health data (CSV)", type=["csv"], key="sidebar_file_uploader", help="Upload CSV files with health data")
        
        # Process uploaded file if any
        if uploaded_file is not None and "last_uploaded_file" not in st.session_state:
            st.session_state.last_uploaded_file = uploaded_file.name
            with st.spinner("Processing your data..."):
                try:
                    import pandas as pd
                    
                    # Read the CSV data
                    df = pd.read_csv(uploaded_file)
                    
                    # Automatically detect data type based on columns
                    data_type = "unknown"
                    columns = set(df.columns.str.lower())
                    
                    if {"sleep_hours", "deep_sleep", "rem_sleep", "light_sleep"}.intersection(columns):
                        data_type = "sleep"
                    elif {"steps", "active_calories", "exercise_minutes"}.intersection(columns):
                        data_type = "exercise"
                    elif {"calories", "protein", "carbs", "fats"}.intersection(columns):
                        data_type = "nutrition"
                    elif {"weight", "systolic", "diastolic", "body_fat_percentage"}.intersection(columns):
                        data_type = "biometric"
                    
                    # Convert DataFrame to dictionary format expected by the router
                    data_dict = {
                        f"{data_type}_data": df.to_dict(orient="records")
                    }
                    
                    # Create a prompt about the uploaded data
                    file_name = uploaded_file.name
                    data_prompt = f"I've just uploaded my health data file '{file_name}'. Can you analyze it and give me insights?"
                    
                    # Add user message
                    st.session_state.messages.append({"role": "user", "content": data_prompt})
                    
                    # Process the data upload with the coach
                    response = await st.session_state.coach.handle_data_upload(data_type, data_dict)
                    
                    # Force update of the active context in session state
                    update_session_context()
                    
                    # Ensure we have a valid response
                    if response is None:
                        response = {
                            "response": f"I've processed your {data_type} data and created an observation context. You can now ask me questions about your {data_type} data.",
                            "insights": [f"Successfully processed {data_type} data from {file_name}"]
                        }
                    elif isinstance(response, str):
                        # Convert string response to dict format
                        response = {
                            "response": response,
                            "insights": [f"Successfully processed {data_type} data from {file_name}"]
                        }
                    elif isinstance(response, dict) and "response" not in response:
                        # Add a default response if missing
                        response["response"] = f"I've processed your {data_type} data and created an observation context. You can now ask me questions about your {data_type} data."
                        if "insights" not in response:
                            response["insights"] = [f"Successfully processed {data_type} data from {file_name}"]
                    
                    # Log the response for debugging
                    print(f"UI Response to display: {response}")
                    
                    # Create a clean copy of the response for the session state
                    # This ensures we don't have any None values that might be displayed
                    clean_response = {
                        "response": response.get("response", f"I've processed your {data_type} data and created an observation context."),
                        "insights": response.get("insights", [f"Successfully processed {data_type} data from {file_name}"]),
                        "visualization": response.get("visualization", None),
                        "error": response.get("error", None)
                    }
                    
                    # Add assistant response to session state with the clean response
                    st.session_state.messages.append({"role": "assistant", "content": clean_response})
                    
                    # Success message
                    st.success(f"Successfully processed your {data_type} data!")
                    
                except Exception as e:
                    st.error(f"Error processing data: {str(e)}")
                    print(f"Data processing error: {str(e)}")
                    
                # Force a rerun to update the display
                st.rerun()
        
        # Reset the last uploaded file if a new file is uploaded
        if uploaded_file is not None and "last_uploaded_file" in st.session_state:
            if uploaded_file.name != st.session_state.last_uploaded_file:
                del st.session_state.last_uploaded_file
                st.rerun()
        
        # Display current context
        if st.session_state.user_data_loaded and st.session_state.coach:
            st.header("Current Context")
            
            # Get active context from session state
            active_context = st.session_state.active_context
            
            # Display active topic
            active_topic = active_context.get('active_topic')
            if active_topic:
                st.info(f"Active Topic: {active_topic}")
            else:
                st.info("Active Topic: General")
            
            # Display observation contexts
            observation_contexts = active_context.get('observation_contexts', {})
            if observation_contexts:
                st.subheader("Observation Contexts")
                for agent_name, context in observation_contexts.items():
                    data_type = context.get('data_type', 'unknown')
                    relevancy = context.get('relevancy_score', 0.0)
                    confidence = context.get('confidence_score', 0.0)
                    
                    # Create a colored indicator based on relevancy score
                    if relevancy > 0.7:
                        color = "🟢"  # High relevancy
                    elif relevancy > 0.4:
                        color = "🟡"  # Medium relevancy
                    else:
                        color = "⚪"  # Low relevancy
                    
                    st.markdown(f"{color} **{data_type.capitalize()}** (Agent: {agent_name})")
                    st.progress(relevancy)
                    st.caption(f"Relevancy: {relevancy:.2f} | Confidence: {confidence:.2f}")
            else:
                st.caption("No active observation contexts")

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
                    # Debug log the content
                    print(f"Rendering message content: {content}")
                    
                    # Handle error if present
                    if "error" in content and content["error"]:
                        st.error(content["error"])
                        continue
                    
                    # Always display response text first if available
                    if "response" in content and content["response"]:
                        st.markdown(content["response"])
                    elif content:
                        # If no response field but content exists, display a default message
                        st.markdown("I've processed your data and created an observation context. You can now ask me questions about your data.")
                    
                    # Handle visualization if present
                    if "visualization" in content and content["visualization"]:
                        try:
                            viz_data = content["visualization"]
                            # Determine visualization type
                            viz_type = "line"  # Default type
                            if "viz_type" in viz_data:
                                viz_type = viz_data["viz_type"]
                            elif "categories" in viz_data and "values" in viz_data:
                                if len(viz_data["categories"]) > 5:
                                    viz_type = "bar"
                                else:
                                    viz_type = "radar"
                            elif "data_matrix" in viz_data:
                                viz_type = "heatmap"
                            
                            # Create the visualization
                            fig = create_visualization(viz_data, viz_type)
                            if fig:
                                # Use Streamlit's pyplot function with clear_figure=False to prevent auto-clearing
                                st.pyplot(fig, clear_figure=False)
                                # Close the figure to free memory
                                plt.close(fig)
                        except Exception as e:
                            st.error(f"Error displaying visualization: {str(e)}")
                    
                    # Display insights if present
                    if "insights" in content and content["insights"]:
                        st.markdown("### Key Insights")
                        for insight in content["insights"]:
                            st.markdown(f"- {insight}")
                    
                    # Display recommendations if present
                    if "recommendations" in content and content["recommendations"]:
                        st.markdown("### Recommendations")
                        for recommendation in content["recommendations"]:
                            st.markdown(f"- {recommendation}")
                    
                    # Display questions if present
                    if "questions" in content and content["questions"]:
                        st.markdown("### Questions")
                        for question in content["questions"]:
                            st.markdown(f"- {question}")
                elif message.get("content") is None:
                    # Handle None content explicitly
                    st.markdown("I've processed your data and created an observation context. You can now ask me questions about your data.")
                else:
                    # Handle string content
                    st.markdown(message["content"])
        
        # Create a more aesthetic chat input with file upload above
        chat_container = st.container()
        
        # Add custom CSS for a more aesthetic input area
        st.markdown("""
        <style>
        .chat-input-container {
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 8px;
            background-color: #f9f9f9;
            margin-bottom: 10px;
        }
        .file-upload-container {
            display: flex;
            align-items: center;
            margin-bottom: 10px;
        }
        .file-upload-icon {
            color: #555;
            margin-right: 5px;
            font-size: 18px;
        }
        .file-upload-text {
            color: #555;
            font-size: 14px;
            margin-right: 10px;
        }
        .send-button {
            margin-top: 5px;
            width: 100%;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Chat input below the file upload
        prompt = st.text_input("Type your message here...", key="chat_prompt")
        
        # Add a send button
        send_button = st.button("Send", key="send_button", help="Send your message", use_container_width=True)
        
        # Process user input when send button is clicked
        if prompt and send_button:
            # Add user message
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Get assistant response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = await st.session_state.coach.process_message(prompt)
                    
                    # Update the active context in session state
                    update_session_context()
                    
                    # Ensure we have a valid response
                    if response is None:
                        response = {
                            "response": "I processed your message but couldn't generate a specific response. Please try rephrasing your question.",
                            "insights": []
                        }
                    elif isinstance(response, str):
                        # Convert string response to dict format
                        response = {
                            "response": response,
                            "insights": []
                        }
                    elif isinstance(response, dict) and "response" not in response:
                        # Add a default response if missing
                        response["response"] = "I processed your message but the response format was unexpected. Please try asking a different question."
                        if "insights" not in response:
                            response["insights"] = []
                    
                    # Log the response for debugging
                    print(f"UI Response to display: {response}")
                    
                    # Create a clean copy of the response for the session state
                    # This ensures we don't have any None values that might be displayed
                    clean_response = {
                        "response": response.get("response", "I processed your message but couldn't generate a specific response."),
                        "insights": response.get("insights", []),
                        "visualization": response.get("visualization", None),
                        "error": response.get("error", None)
                    }
                    
                    # Add to session state messages with the clean response
                    st.session_state.messages.append({"role": "assistant", "content": clean_response})
                    
                    # Display the response directly (don't rely on the message rendering)
                    if isinstance(response, dict):
                        # Always display response text first if available
                        if "response" in response and response["response"]:
                            st.markdown(response["response"])
                        else:
                            # If no response field, display a default message
                            st.markdown("I processed your message but couldn't generate a specific response. Please try rephrasing your question.")
                        
                        # Handle error if present
                        if "error" in response and response["error"]:
                            st.error(response["error"])
                        
                        # Handle visualization if present
                        if "visualization" in response and response["visualization"]:
                            try:
                                viz_data = response["visualization"]
                                # Determine visualization type
                                viz_type = "line"  # Default type
                                if "viz_type" in viz_data:
                                    viz_type = viz_data["viz_type"]
                                elif "categories" in viz_data and "values" in viz_data:
                                    if len(viz_data["categories"]) > 5:
                                        viz_type = "bar"
                                    else:
                                        viz_type = "radar"
                                elif "data_matrix" in viz_data:
                                    viz_type = "heatmap"
                                
                                # Create the visualization
                                fig = create_visualization(viz_data, viz_type)
                                if fig:
                                    # Use Streamlit's pyplot function with clear_figure=False
                                    st.pyplot(fig, clear_figure=False)
                                    # Close the figure to free memory
                                    plt.close(fig)
                            except Exception as e:
                                st.error(f"Error displaying visualization: {str(e)}")
                                print(f"Visualization error: {str(e)}")
                        
                        # Display insights if present
                        if "insights" in response and response["insights"]:
                            st.markdown("### Key Insights")
                            for insight in response["insights"]:
                                st.markdown(f"- {insight}")
                        
                        # Display recommendations if present
                        if "recommendations" in response and response["recommendations"]:
                            st.markdown("### Recommendations")
                            for recommendation in response["recommendations"]:
                                st.markdown(f"- {recommendation}")
                        
                        # Display questions if present
                        if "questions" in response and response["questions"]:
                            st.markdown("### Questions")
                            for question in response["questions"]:
                                st.markdown(f"- {question}")
                    else:
                        # If response is not a dict, convert to string and display
                        st.markdown(str(response))
            
            # Force a rerun to update the display
            st.rerun()
    else:
        st.info("Please select a user to begin.")

if __name__ == "__main__":
    asyncio.run(main()) 