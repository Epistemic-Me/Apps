"""
Factory functions for creating router components.

This module provides factory functions for creating semantic router and router adapter instances.
"""

import asyncio
from typing import List, Dict, Any, Optional

from bio_age_coach.agents.base_agent import Agent
from bio_age_coach.agents.agent_registry import AgentRegistry
from bio_age_coach.router.semantic_router import SemanticRouter
from bio_age_coach.router.router_adapter import RouterAdapter

async def create_semantic_router(
    api_key: str,
    agents: Optional[List[Agent]] = None,
    agent_registry: Optional[AgentRegistry] = None
) -> SemanticRouter:
    """Create a semantic router instance.
    
    Args:
        api_key: OpenAI API key for embeddings
        agents: List of agent instances (optional if agent_registry is provided)
        agent_registry: Agent registry instance (optional if agents is provided)
        
    Returns:
        SemanticRouter: Initialized semantic router
        
    Raises:
        ValueError: If neither agents nor agent_registry is provided
    """
    if not agents and not agent_registry:
        raise ValueError("Either agents or agent_registry must be provided")
    
    # If agent_registry is provided but not agents, get agents from registry
    if not agents and agent_registry:
        agents = agent_registry.get_all_agents()
    
    # Create and initialize the semantic router
    router = SemanticRouter(api_key=api_key, agents=agents)
    
    return router

async def create_router_adapter(
    api_key: str,
    agents: Optional[List[Agent]] = None,
    agent_registry: Optional[AgentRegistry] = None
) -> RouterAdapter:
    """Create a router adapter instance.
    
    Args:
        api_key: OpenAI API key for embeddings
        agents: List of agent instances (optional if agent_registry is provided)
        agent_registry: Agent registry instance (optional if agents is provided)
        
    Returns:
        RouterAdapter: Initialized router adapter
        
    Raises:
        ValueError: If neither agents nor agent_registry is provided
    """
    # Create the semantic router
    semantic_router = await create_semantic_router(
        api_key=api_key,
        agents=agents,
        agent_registry=agent_registry
    )
    
    # Create the router adapter
    adapter = RouterAdapter(semantic_router=semantic_router)
    
    return adapter

async def initialize_router_system(
    api_key: str,
    agent_registry: Optional[AgentRegistry] = None
) -> Dict[str, Any]:
    """Initialize the complete router system.
    
    This function initializes the agent registry (if not provided),
    creates a semantic router, and wraps it in a router adapter.
    
    Args:
        api_key: OpenAI API key for embeddings
        agent_registry: Optional pre-initialized agent registry
        
    Returns:
        Dict[str, Any]: Dictionary containing the initialized components
            - agent_registry: The agent registry
            - semantic_router: The semantic router
            - router_adapter: The router adapter
    """
    # Initialize agent registry if not provided
    if not agent_registry:
        agent_registry = AgentRegistry()
        await agent_registry.initialize(api_key)
    
    # Get all agents from the registry
    agents = agent_registry.get_all_agents()
    
    # Create the semantic router
    semantic_router = await create_semantic_router(
        api_key=api_key,
        agents=agents
    )
    
    # Create the router adapter
    router_adapter = RouterAdapter(semantic_router=semantic_router)
    
    return {
        "agent_registry": agent_registry,
        "semantic_router": semantic_router,
        "router_adapter": router_adapter
    } 