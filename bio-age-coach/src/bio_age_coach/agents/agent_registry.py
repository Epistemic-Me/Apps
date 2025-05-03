"""Registry for managing Bio-Age Coach agents."""

from typing import Dict, List, Optional, Type, Any
from .base_agent import Agent
from bio_age_coach.mcp.client import MultiServerMCPClient

class AgentRegistry:
    """Registry for managing Bio-Age Coach agents."""
    
    def __init__(self, api_key: str, mcp_client: MultiServerMCPClient):
        """Initialize the agent registry.
        
        Args:
            api_key: OpenAI API key
            mcp_client: MCP client for server communication
        """
        self.api_key = api_key
        self.mcp_client = mcp_client
        self.agents: Dict[str, Agent] = {}
        self.agent_types: Dict[str, Type[Agent]] = {}

    def register_agent_type(self, name: str, agent_class: Type[Agent]) -> None:
        """Register an agent type.
        
        Args:
            name: Name of the agent type
            agent_class: Agent class to register
        """
        self.agent_types[name] = agent_class

    def create_agent(self, name: str, agent_type: str, **kwargs) -> Agent:
        """Create and register a new agent.
        
        Args:
            name: Name for the new agent instance
            agent_type: Type of agent to create
            **kwargs: Additional arguments for agent initialization
            
        Returns:
            Agent: Created agent instance
            
        Raises:
            ValueError: If agent_type is not registered
        """
        if agent_type not in self.agent_types:
            raise ValueError(f"Agent type {agent_type} not registered")
            
        agent_class = self.agent_types[agent_type]
        
        # Default description if not provided
        if 'description' not in kwargs:
            kwargs['description'] = f"{agent_type.title()} Agent"
            
        agent = agent_class(
            name=name,
            api_key=self.api_key,
            mcp_client=self.mcp_client,
            **kwargs
        )
        self.agents[name] = agent
        return agent

    def get_agent(self, name: str) -> Optional[Agent]:
        """Get an agent by name.
        
        Args:
            name: Name of the agent
            
        Returns:
            Optional[Agent]: Agent instance if found, None otherwise
        """
        return self.agents.get(name)

    def get_all_agents(self) -> List[Agent]:
        """Get all registered agents.
        
        Returns:
            List[Agent]: List of all registered agents
        """
        return list(self.agents.values())

    async def find_best_agent(self, query: str, context: Dict[str, Any]) -> Optional[Agent]:
        """Find the best agent to handle a query.
        
        Args:
            query: User query
            context: Conversation context
            
        Returns:
            Optional[Agent]: Best agent for the query, or None if no agent is suitable
        """
        best_agent = None
        best_score = 0.0
        
        for agent in self.agents.values():
            score = await agent.can_handle(query, context)
            if score > best_score:
                best_score = score
                best_agent = agent
                
        return best_agent if best_score > 0.5 else None  # Only return agent if confidence > 0.5

    async def process_query(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process a query using the best available agent.
        
        Args:
            query: User query
            context: Conversation context
            
        Returns:
            Dict[str, Any]: Response from the agent
            
        Raises:
            ValueError: If no suitable agent is found
        """
        agent = await self.find_best_agent(query, context)
        if not agent:
            raise ValueError("No suitable agent found for query")
        return await agent.process(query, context)

    async def close(self) -> None:
        """Close all registered agents."""
        for agent in self.agents.values():
            await agent.close() 