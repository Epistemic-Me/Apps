"""
Debug script to test the semantic router directly.
"""

import os
import asyncio
from dotenv import load_dotenv
from bio_age_coach.mcp.utils.client import MultiServerMCPClient
from bio_age_coach.mcp.servers.health_server import HealthServer
from bio_age_coach.mcp.servers.research_server import ResearchServer
from bio_age_coach.mcp.servers.tools_server import ToolsServer
from bio_age_coach.mcp.servers.bio_age_score_server import BioAgeScoreServer
from bio_age_coach.agents.factory import create_agents
from bio_age_coach.router.semantic_router import SemanticRouter

# Load environment variables
load_dotenv()

async def test_router():
    """Test the semantic router with a simple query."""
    print("Testing semantic router...")
    api_key = os.getenv("OPENAI_API_KEY", "default_key")
    
    # Adjust path to account for script being in scripts/debug directory
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    papers_dir = os.path.join(project_root, "data/papers")
    test_data_path = os.path.join(project_root, "data/test_health_data")

    # Initialize test users
    test_users = [
        {"id": "test_user_1", "username": "Test User 1"}
    ]
    
    # Create MCP client
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
    
    # Create agents
    print("Creating agents...")
    agents = create_agents(api_key, mcp_client)
    
    # Create semantic router
    print("Creating semantic router...")
    router = SemanticRouter(api_key=api_key, agents=agents)
    
    # Test query
    test_query = "What is biological age?"
    user_id = "test_user_1"
    
    print(f"\nRouting query: '{test_query}'")
    response = await router.route_query(user_id=user_id, query=test_query)
    
    print("\nResponse:")
    print(f"  Response text: {response.get('response')}")
    print(f"  Insights: {response.get('insights')}")
    print(f"  Error: {response.get('error')}")
    
    # Test another query
    test_query = "How is my sleep quality?"
    print(f"\nRouting query: '{test_query}'")
    response = await router.route_query(user_id=user_id, query=test_query)
    
    print("\nResponse:")
    print(f"  Response text: {response.get('response')}")
    print(f"  Insights: {response.get('insights')}")
    print(f"  Error: {response.get('error')}")

if __name__ == "__main__":
    asyncio.run(test_router()) 