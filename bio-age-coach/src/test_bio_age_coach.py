"""
Test script for BioAgeCoach visualization functionality.
"""

import asyncio
import json
import os
import pandas as pd
from datetime import datetime, timedelta
from bio_age_coach.chatbot.coach import BioAgeCoach
from bio_age_coach.mcp.client import MultiServerMCPClient
from bio_age_coach.mcp.router import QueryRouter
from bio_age_coach.mcp.health_server import HealthServer
from bio_age_coach.mcp.bio_age_score_server import BioAgeScoreServer
from bio_age_coach.mcp.research_server import ResearchServer
from bio_age_coach.mcp.tools_server import ToolsServer
from test_bio_age_score_server import process_workout_data

async def test_coach_visualization():
    """Test the bio-age coach's visualization functionality."""
    print("✓ Initializing test environment...")
    
    # Initialize servers
    api_key = "test_key_123"
    health_server = HealthServer(api_key)
    bio_age_score_server = BioAgeScoreServer(api_key)
    research_server = ResearchServer(api_key)
    tools_server = ToolsServer(api_key)
    
    # Initialize MCP client
    mcp_client = MultiServerMCPClient(
        health_server=health_server,
        bio_age_score_server=bio_age_score_server,
        research_server=research_server,
        tools_server=tools_server
    )
    
    # Initialize router
    query_router = QueryRouter(
        health_server=health_server,
        research_server=research_server,
        tools_server=tools_server,
        bio_age_score_server=bio_age_score_server
    )
    
    # Create coach
    coach = BioAgeCoach(mcp_client, query_router)
    print("✓ Coach initialized")
    
    # Load test data
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'test_health_data')
    daily_metrics = process_workout_data(data_dir)
    
    # Format health data
    health_data = {"health_data": daily_metrics}
    
    # Initialize servers with test data
    await health_server.initialize_data(health_data)
    await bio_age_score_server.initialize_data(health_data)
    
    # Store data in coach
    coach.user_data = {
        "health_data": daily_metrics,
        "habits": {},
        "plan": {},
        "bio_age_tests": {},
        "capabilities": {},
        "biomarkers": {},
        "measurements": {},
        "lab_results": {},
        "age": None,
        "sex": None
    }
    print(f"✓ Loaded {len(daily_metrics)} days of health data")
    
    try:
        # Test visualization query
        query = "Can you show me how my bio-age scores have been trending over the last 30 days?"
        print("\nUser query:", query)
        
        # First, calculate scores
        scores_response = await mcp_client.send_request(
            "bio_age_score",
            {
                "type": "calculate_30_day_scores",
                "data": health_data
            }
        )
        
        if isinstance(scores_response, dict) and "scores" in scores_response:
            # Then, create visualization
            viz_response = await mcp_client.send_request(
                "bio_age_score",
                {
                    "type": "visualization",
                    "data": health_data
                }
            )
            
            if isinstance(viz_response, dict) and "visualization" in viz_response:
                coach.user_data["visualization"] = viz_response["visualization"]
        
        # Process the query
        response = await coach.process_message(query)
        print("\nCoach response:")
        print(response)
        
        # Verify visualization data
        if "visualization" in coach.user_data:
            viz_data = coach.user_data["visualization"]
            print("\n✓ Visualization data generated successfully")
            if "reference_ranges" in viz_data:
                print("Reference ranges:")
                for range_name, range_data in viz_data["reference_ranges"].items():
                    print(f"  {range_name}: {range_data['min']}-{range_data['max']}")
            
            # Print figure data if available
            if "figure" in viz_data:
                print("\nVisualization figure data available")
                print("- Contains plotly figure data for rendering")
                
            # Print insights if available
            if "insights" in viz_data:
                print("\nVisualization insights:")
                for insight in viz_data["insights"]:
                    print(f"- {insight}")
        else:
            print("\n❌ No visualization data generated")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(test_coach_visualization()) 