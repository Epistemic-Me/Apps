"""
Test script to verify agent initialization without starting the Streamlit server.
This script focuses specifically on testing the agent creation process.
"""

import os
import asyncio
from dotenv import load_dotenv
from bio_age_coach.mcp.utils.client import MultiServerMCPClient
from bio_age_coach.agents.factory import create_agents
from bio_age_coach.agents.specialized.bio_age_score_agent import BioAgeScoreAgent
from bio_age_coach.agents.specialized.health_data_agent import HealthDataAgent
from bio_age_coach.agents.specialized.research_agent import ResearchAgent
from bio_age_coach.agents.specialized.general_agent import GeneralAgent

# Load environment variables
load_dotenv()

def test_agent_factory():
    """Test the agent factory."""
    print("Testing agent factory...")
    api_key = os.getenv("OPENAI_API_KEY", "default_key")
    mcp_client = MultiServerMCPClient(api_key=api_key)
    
    try:
        agents = create_agents(api_key, mcp_client)
        print(f"Successfully created {len(agents)} agents:")
        for agent in agents:
            print(f"  - {agent.name}: {agent.description}")
        return True
    except Exception as e:
        print(f"Error creating agents: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_individual_agents():
    """Test creating each agent individually."""
    print("\nTesting individual agent creation...")
    api_key = os.getenv("OPENAI_API_KEY", "default_key")
    mcp_client = MultiServerMCPClient(api_key=api_key)
    
    all_passed = True
    
    # Test BioAgeScoreAgent
    try:
        print("Creating BioAgeScoreAgent...")
        agent = BioAgeScoreAgent(
            name="BioAgeScoreAgent",
            description="I analyze health metrics to calculate and explain biological age scores.",
            api_key=api_key,
            mcp_client=mcp_client
        )
        print(f"  - Success: {agent.name}")
    except Exception as e:
        print(f"  - Error creating BioAgeScoreAgent: {str(e)}")
        all_passed = False
    
    # Test HealthDataAgent
    try:
        print("Creating HealthDataAgent...")
        agent = HealthDataAgent(
            name="HealthDataAgent",
            description="I process and analyze health data to provide insights and recommendations.",
            api_key=api_key,
            mcp_client=mcp_client
        )
        print(f"  - Success: {agent.name}")
    except Exception as e:
        print(f"  - Error creating HealthDataAgent: {str(e)}")
        all_passed = False
    
    # Test ResearchAgent
    try:
        print("Creating ResearchAgent...")
        agent = ResearchAgent(
            name="ResearchAgent",
            description="I provide research-based information on health, longevity, and biological age.",
            api_key=api_key,
            mcp_client=mcp_client
        )
        print(f"  - Success: {agent.name}")
    except Exception as e:
        print(f"  - Error creating ResearchAgent: {str(e)}")
        all_passed = False
    
    # Test GeneralAgent
    try:
        print("Creating GeneralAgent...")
        agent = GeneralAgent(
            name="GeneralAgent",
            description="I handle general queries about the Bio Age Coach system and provide basic assistance.",
            api_key=api_key,
            mcp_client=mcp_client
        )
        print(f"  - Success: {agent.name}")
    except Exception as e:
        print(f"  - Error creating GeneralAgent: {str(e)}")
        all_passed = False
    
    return all_passed

def main():
    """Main function to test agent initialization."""
    print("Starting agent initialization tests...\n")
    
    factory_test_passed = test_agent_factory()
    individual_tests_passed = test_individual_agents()
    
    if factory_test_passed and individual_tests_passed:
        print("\nAll agent initialization tests passed successfully!")
    else:
        print("\nSome agent initialization tests failed. See errors above.")

if __name__ == "__main__":
    main() 