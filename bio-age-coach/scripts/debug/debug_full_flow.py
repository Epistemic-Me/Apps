"""
Test script for the full flow with data upload and querying.
"""

import os
import asyncio
import json
from dotenv import load_dotenv
from bio_age_coach.mcp.utils.client import MultiServerMCPClient
from bio_age_coach.mcp.core.module_registry import ModuleRegistry
from bio_age_coach.mcp.servers.health_server import HealthServer
from bio_age_coach.mcp.servers.research_server import ResearchServer
from bio_age_coach.mcp.servers.tools_server import ToolsServer
from bio_age_coach.mcp.servers.bio_age_score_server import BioAgeScoreServer
from bio_age_coach.router.router_adapter import RouterAdapter
from bio_age_coach.router.semantic_router import SemanticRouter
from bio_age_coach.agents.factory import create_agents
from bio_age_coach.chatbot.coach import BioAgeCoach

# Load environment variables
load_dotenv()

async def init_mcp_servers():
    """Initialize MCP servers and conversation modules."""
    print("Initializing MCP servers...")
    api_key = os.getenv("OPENAI_API_KEY", "default_key")
    # Adjust path to account for script being in scripts/debug directory
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    papers_dir = os.path.join(project_root, "data/papers")
    test_data_path = os.path.join(project_root, "data/test_health_data")

    # Initialize test users
    test_users = [
        {"id": "test_user_1", "username": "Test User 1"}
    ]

    # Create MCP client first
    print("Creating MCP client...")
    mcp_client = MultiServerMCPClient(api_key=api_key)

    # Initialize servers
    print("Initializing servers...")
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
    print("Registering servers with MCP client...")
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
    print("Creating agents...")
    agents = create_agents(api_key, mcp_client)
    
    # Create semantic router with agents
    print("Creating semantic router...")
    semantic_router = SemanticRouter(api_key=api_key, agents=agents)
    
    # Create router adapter with semantic router
    print("Creating router adapter...")
    router_adapter = RouterAdapter(
        semantic_router=semantic_router,
        mcp_client=mcp_client,
        module_registry=module_registry
    )

    # Create BioAgeCoach instance
    print("Creating BioAgeCoach instance...")
    coach = await BioAgeCoach.create(mcp_client, router_adapter)
    
    print("Initialization complete!")
    return mcp_client, router_adapter, coach, semantic_router, agents

async def test_full_flow():
    """Test the full flow with data upload and querying."""
    print("\nTesting full flow with data upload and querying...")
    
    mcp_client, router_adapter, coach, semantic_router, agents = await init_mcp_servers()
    
    # Set user ID
    user_id = "test_user_1"
    coach.user_id = user_id
    
    # Create test data for upload
    sleep_data = {
        "data": {
            "sleep_data": [
                {
                    "date": "2023-01-01",
                    "sleep_hours": 7.5,
                    "deep_sleep": 1.2,
                    "rem_sleep": 2.0,
                    "light_sleep": 4.3
                }
            ]
        },
        "data_type": "sleep",
        "data_upload": True
    }
    
    # Upload sleep data
    print("\nUploading sleep data...")
    response = await router_adapter.route_query(
        user_id=user_id,
        query="Here's my sleep data for analysis",
        metadata=sleep_data
    )
    
    print("\nResponse to sleep data upload:")
    print(f"Response: {response.get('response')}")
    print(f"Insights: {response.get('insights')}")
    
    # Print observation contexts
    print("\nObservation contexts after sleep data upload:")
    for agent_name, context in semantic_router.observation_contexts.get(user_id, {}).items():
        print(f"Agent: {agent_name}")
        print(f"  Context type: {type(context).__name__}")
        print(f"  Data type: {context.data_type}")
        print(f"  Relevancy score: {context.relevancy_score}")
        print(f"  Confidence score: {context.confidence_score}")
    
    # Test sleep query
    sleep_query = "How has my sleep quality been?"
    print(f"\nQuerying: '{sleep_query}'")
    
    # Calculate relevancy scores for each agent's observation context
    print("\nRelevancy scores for sleep query:")
    for agent_name, context in semantic_router.observation_contexts.get(user_id, {}).items():
        relevancy = context.calculate_relevancy(sleep_query)
        print(f"Agent: {agent_name}, Relevancy: {relevancy}")
    
    # Route the query
    response = await router_adapter.route_query(
        user_id=user_id,
        query=sleep_query
    )
    
    print("\nResponse to sleep query:")
    print(f"Response: {response.get('response')}")
    print(f"Insights: {response.get('insights')}")
    
    # Create exercise data for upload
    exercise_data = {
        "data": {
            "exercise_data": [
                {
                    "date": "2023-01-01",
                    "steps": 8000,
                    "active_calories": 400,
                    "workout_minutes": 45,
                    "heart_rate": 140
                }
            ]
        },
        "data_type": "exercise",
        "data_upload": True
    }
    
    # Upload exercise data
    print("\nUploading exercise data...")
    response = await router_adapter.route_query(
        user_id=user_id,
        query="Here's my exercise data for analysis",
        metadata=exercise_data
    )
    
    print("\nResponse to exercise data upload:")
    print(f"Response: {response.get('response')}")
    print(f"Insights: {response.get('insights')}")
    
    # Print observation contexts
    print("\nObservation contexts after exercise data upload:")
    for agent_name, context in semantic_router.observation_contexts.get(user_id, {}).items():
        print(f"Agent: {agent_name}")
        print(f"  Context type: {type(context).__name__}")
        print(f"  Data type: {context.data_type}")
        print(f"  Relevancy score: {context.relevancy_score}")
        print(f"  Confidence score: {context.confidence_score}")
    
    # Test exercise query
    exercise_query = "How many calories did I burn during my workouts?"
    print(f"\nQuerying: '{exercise_query}'")
    
    # Calculate relevancy scores for each agent's observation context
    print("\nRelevancy scores for exercise query:")
    for agent_name, context in semantic_router.observation_contexts.get(user_id, {}).items():
        relevancy = context.calculate_relevancy(exercise_query)
        print(f"Agent: {agent_name}, Relevancy: {relevancy}")
    
    # Route the query
    response = await router_adapter.route_query(
        user_id=user_id,
        query=exercise_query
    )
    
    print("\nResponse to exercise query:")
    print(f"Response: {response.get('response')}")
    print(f"Insights: {response.get('insights')}")
    
    # Test general query
    general_query = "What is biological age?"
    print(f"\nQuerying: '{general_query}'")
    
    # Calculate relevancy scores for each agent's observation context
    print("\nRelevancy scores for general query:")
    for agent_name, context in semantic_router.observation_contexts.get(user_id, {}).items():
        relevancy = context.calculate_relevancy(general_query)
        print(f"Agent: {agent_name}, Relevancy: {relevancy}")
    
    # Route the query
    response = await router_adapter.route_query(
        user_id=user_id,
        query=general_query
    )
    
    print("\nResponse to general query:")
    print(f"Response: {response.get('response')}")
    print(f"Insights: {response.get('insights')}")

async def main():
    """Main function to test the full flow."""
    await test_full_flow()

if __name__ == "__main__":
    asyncio.run(main()) 