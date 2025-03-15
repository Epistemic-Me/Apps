"""
Debug script to test data upload and querying.

This script simulates the browser interaction by:
1. Initializing the MCP servers and coach
2. Uploading sample data files
3. Checking if the observation context is updated
4. Sending a query about the uploaded data
5. Verifying the response
"""

import os
import asyncio
import json
import pandas as pd
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
    papers_dir = "data/papers"
    test_data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data/test_health_data")

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

    print("MCP servers initialized successfully")
    return mcp_client, router_adapter

async def debug_data_upload():
    """Debug data upload and querying."""
    print("\n=== Starting debug_data_upload test ===")
    mcp_client, router_adapter = await init_mcp_servers()
    
    print("\nCreating coach...")
    coach = await BioAgeCoach.create(mcp_client, router_adapter)
    
    # Path to sample data files
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
    
    # Test with different data types
    data_types = ["sleep", "exercise", "nutrition", "biometric"]
    
    for data_type in data_types:
        print(f"\n=== Testing {data_type} data upload ===")
        
        # Use the sample data files
        sample_file = os.path.join(data_dir, f"sample_{data_type}_data.csv")
        
        if not os.path.exists(sample_file):
            print(f"Sample file not found: {sample_file}")
            continue
            
        print(f"Using sample file: {sample_file}")
        
        # Read the CSV file
        df = pd.read_csv(sample_file)
        print(f"CSV columns: {df.columns.tolist()}")
        print(f"Sample data:\n{df.head(2)}")
        
        # Convert to dictionary format
        data_dict = {
            f"{data_type}_data": df.to_dict(orient="records")
        }
        
        # Get initial active context
        print("\nInitial active context:")
        initial_context = coach.get_active_context()
        print(json.dumps(initial_context, indent=2))
        
        # Process the data upload
        print(f"\nUploading {data_type} data...")
        response = await coach.handle_data_upload(data_type, data_dict)
        
        # Check the response
        print(f"\nResponse from handle_data_upload:")
        if response is None:
            print("ERROR: Received None response")
        else:
            print(f"Response type: {type(response)}")
            if isinstance(response, dict):
                print(json.dumps(response, indent=2))
        
        # Check if observation context was updated
        print("\nChecking if observation context was updated:")
        active_context = coach.get_active_context()
        print(json.dumps(active_context, indent=2))
        
        # Check if the observation context contains the data type
        observation_contexts = active_context.get('observation_contexts', {})
        has_context = any(context.get('data_type') == data_type for context in observation_contexts.values())
        print(f"Has {data_type} observation context: {has_context}")
        
        # Now test querying about the uploaded data
        print(f"\nQuerying about {data_type} data...")
        query = f"Can you analyze my {data_type} data and give me insights?"
        query_response = await coach.process_message(query)
        
        # Check the query response
        print(f"\nResponse from process_message:")
        if query_response is None:
            print("ERROR: Received None query response")
        else:
            print(f"Response type: {type(query_response)}")
            if isinstance(query_response, dict):
                # Print a truncated version of the response text
                if "response" in query_response:
                    response_text = query_response["response"]
                    print(f"Response text: {response_text[:200]}..." if len(response_text) > 200 else response_text)
                if "insights" in query_response:
                    print(f"Insights: {query_response['insights']}")
        
        # Check if observation context was updated after query
        print("\nChecking if observation context was updated after query:")
        post_query_context = coach.get_active_context()
        print(json.dumps(post_query_context, indent=2))
        
        print(f"\n=== End of {data_type} test ===")

if __name__ == "__main__":
    asyncio.run(debug_data_upload()) 