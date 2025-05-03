"""Tests for the AgentRegistry class."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from bio_age_coach.agents.agent_registry import AgentRegistry
from bio_age_coach.agents.base_agent import Agent, AgentState
from bio_age_coach.mcp.client import MultiServerMCPClient
from langchain.schema import AgentAction, AgentFinish
from typing import List, Dict, Any, Tuple, Union, Optional, Set
from langchain.tools import BaseTool

# Create a mock Agent class that doesn't inherit from AgentExecutor
class TestAgent:
    """Test implementation of Agent for testing purposes."""
    
    def __init__(
        self,
        name: str,
        description: str,
        api_key: str,
        mcp_client: MultiServerMCPClient,
        tools: Optional[List[BaseTool]] = None,
        **kwargs
    ):
        """Initialize the agent.
        
        Args:
            name: Name of the agent
            description: Description of the agent's capabilities
            api_key: OpenAI API key
            mcp_client: MCP client for server communication
            tools: List of tools available to the agent
            **kwargs: Additional arguments for parent class
        """
        self.name = name
        self.description = description
        self.api_key = api_key
        self.mcp_client = mcp_client
        self.tools = tools or []
        self.state: Dict[str, Any] = {}
        self.capabilities: List[str] = []
        self.server_types: Set[str] = set()  # Tracks all server types this agent interacts with
        
        # Initialize agent
        self._initialize_capabilities()
        self._initialize_servers()
        self.state = {"state": AgentState.READY}
    
    def _initialize_capabilities(self) -> None:
        """Initialize agent capabilities."""
        self.capabilities = ["test_capability"]
    
    def _initialize_servers(self) -> None:
        """Initialize server connections."""
        self.server_types = {"test_server"}
    
    async def can_handle(self, query: str, context: dict) -> float:
        return 1.0 if "test" in query.lower() else 0.0
        
    async def process(self, query: str, context: dict) -> dict:
        return {
            "response": "Test response",
            "insights": ["Test insight"],
            "visualization": None,
            "error": None
        }
    
    async def plan(self, intermediate_steps: List[Tuple[AgentAction, str]], **kwargs: Any) -> Union[AgentAction, AgentFinish]:
        """Plan the next action based on intermediate steps."""
        return AgentFinish(
            return_values={"output": "Test plan"},
            log="Test plan log"
        )
    
    async def aplan(self, intermediate_steps: List[Tuple[AgentAction, str]], **kwargs: Any) -> Union[AgentAction, AgentFinish]:
        """Async version of plan."""
        return await self.plan(intermediate_steps, **kwargs)
    
    @property
    def input_keys(self) -> List[str]:
        """Return the input keys required for the agent."""
        return ["input"]
    
    async def send_request(self, server_type: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send a request to a specific server through the MCP client."""
        if server_type not in self.server_types:
            raise ValueError(f"Server type '{server_type}' not registered with agent '{self.name}'")
        
        return await self.mcp_client.send_request(server_type, request_data)
    
    def update_context(self, context_updates: Dict[str, Any]) -> None:
        """Update this agent's context with new information."""
        self.state.update(context_updates)
    
    def get_capabilities(self) -> List[str]:
        """Get the list of capabilities this agent provides."""
        return self.capabilities.copy()
    
    async def close(self) -> None:
        """Clean up agent resources."""
        pass

@pytest.fixture
def mock_mcp_client():
    """Create a mock MCP client."""
    client = Mock(spec=MultiServerMCPClient)
    client.send_request = AsyncMock(return_value={"result": "test"})
    return client

@pytest.fixture
def registry(mock_mcp_client):
    """Create an agent registry instance."""
    return AgentRegistry(api_key="test_key", mcp_client=mock_mcp_client)

def test_registry_initialization(registry):
    """Test registry initialization."""
    assert registry.api_key == "test_key"
    assert isinstance(registry.mcp_client, MultiServerMCPClient)
    assert registry.agents == {}
    assert registry.agent_types == {}

def test_register_agent_type(registry):
    """Test registering an agent type."""
    registry.register_agent_type("test", TestAgent)
    assert registry.agent_types["test"] == TestAgent

def test_create_agent(registry):
    """Test creating an agent."""
    registry.register_agent_type("test", TestAgent)
    agent = registry.create_agent("test_agent", "test")
    assert isinstance(agent, TestAgent)
    assert agent.name == "test_agent"
    assert registry.agents["test_agent"] == agent

def test_create_agent_invalid_type(registry):
    """Test creating an agent with invalid type."""
    with pytest.raises(ValueError):
        registry.create_agent("test_agent", "invalid")

def test_get_agent(registry):
    """Test getting an agent."""
    registry.register_agent_type("test", TestAgent)
    agent = registry.create_agent("test_agent", "test")
    assert registry.get_agent("test_agent") == agent
    assert registry.get_agent("nonexistent") is None

def test_get_all_agents(registry):
    """Test getting all agents."""
    registry.register_agent_type("test", TestAgent)
    agent1 = registry.create_agent("agent1", "test")
    agent2 = registry.create_agent("agent2", "test")
    agents = registry.get_all_agents()
    assert len(agents) == 2
    assert agent1 in agents
    assert agent2 in agents

@pytest.mark.asyncio
async def test_find_best_agent(registry):
    """Test finding the best agent for a query."""
    registry.register_agent_type("test", TestAgent)
    agent = registry.create_agent("test_agent", "test")
    best_agent = await registry.find_best_agent("test query", {})
    assert best_agent == agent
    best_agent = await registry.find_best_agent("other query", {})
    assert best_agent is None

@pytest.mark.asyncio
async def test_process_query(registry):
    """Test processing a query."""
    registry.register_agent_type("test", TestAgent)
    registry.create_agent("test_agent", "test")
    response = await registry.process_query("test query", {})
    assert response["response"] == "Test response"
    assert response["insights"] == ["Test insight"]

@pytest.mark.asyncio
async def test_process_query_no_agent(registry):
    """Test processing a query with no suitable agent."""
    with pytest.raises(ValueError):
        await registry.process_query("test query", {})

@pytest.mark.asyncio
async def test_close(registry):
    """Test closing all agents."""
    registry.register_agent_type("test", TestAgent)
    agent = registry.create_agent("test_agent", "test")
    agent.close = AsyncMock()
    await registry.close()
    agent.close.assert_called_once() 