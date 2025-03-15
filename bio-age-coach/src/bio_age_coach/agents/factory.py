"""Factory module for creating agents.

This module provides functions to create and configure agents for the Bio Age Coach system.
"""

from typing import List
from bio_age_coach.agents.base_agent import Agent
from bio_age_coach.agents.specialized.bio_age_score_agent import BioAgeScoreAgent
from bio_age_coach.agents.specialized.health_data_agent import HealthDataAgent
from bio_age_coach.agents.specialized.research_agent import ResearchAgent
from bio_age_coach.agents.specialized.general_agent import GeneralAgent
from bio_age_coach.mcp.client import MultiServerMCPClient

def create_agents(api_key: str, mcp_client: MultiServerMCPClient) -> List[Agent]:
    """Create and return a list of agent instances.
    
    Args:
        api_key: API key for agents
        mcp_client: MCP client for agent communication
        
    Returns:
        List[Agent]: List of agent instances
    """
    # Create specialized agents
    bio_age_agent = BioAgeScoreAgent(
        name="BioAgeScoreAgent",
        description="I analyze health metrics to calculate and explain biological age scores.",
        api_key=api_key,
        mcp_client=mcp_client
    )
    
    health_data_agent = HealthDataAgent(
        name="HealthDataAgent",
        description="I process and analyze health data to provide insights and recommendations.",
        api_key=api_key,
        mcp_client=mcp_client
    )
    
    research_agent = ResearchAgent(
        name="ResearchAgent",
        description="I provide research-based information on health, longevity, and biological age.",
        api_key=api_key,
        mcp_client=mcp_client
    )
    
    general_agent = GeneralAgent(
        name="GeneralAgent",
        description="I handle general queries about the Bio Age Coach system and provide basic assistance.",
        api_key=api_key,
        mcp_client=mcp_client
    )
    
    # Return list of all agents
    return [
        bio_age_agent,
        health_data_agent,
        research_agent,
        general_agent
    ] 