"""
Test script to verify app initialization without starting the Streamlit server.
This script imports and initializes the key components of the app to check for any errors.
"""

import os
import asyncio
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
    return mcp_client, router_adapter, coach

async def main():
    """Main function to test app initialization."""
    try:
        print("Starting app initialization test...")
        mcp_client, router_adapter, coach = await init_mcp_servers()
        print("App initialization successful!")
        
        # Test a simple query to verify the router works
        print("\nTesting a simple query...")
        response = await coach.process_message("What is biological age?")
        print(f"Response received: {response.get('response', '')[:100]}...")
        
        print("\nAll tests passed successfully!")
    except Exception as e:
        print(f"\nError during initialization: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 