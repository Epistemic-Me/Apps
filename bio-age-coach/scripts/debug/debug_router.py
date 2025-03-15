"""
Debug script to test the semantic router directly.
"""

import os
import asyncio
from dotenv import load_dotenv
from bio_age_coach.mcp.utils.client import MultiServerMCPClient
from bio_age_coach.agents.factory import create_agents
from bio_age_coach.router.semantic_router import SemanticRouter

# Load environment variables
load_dotenv()

async def test_router():
    """Test the semantic router with a simple query."""
    print("Testing semantic router...")
    api_key = os.getenv("OPENAI_API_KEY", "default_key")
    
    # Create MCP client
    mcp_client = MultiServerMCPClient(api_key=api_key)
    
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