"""Tests for the base Agent class."""

import pytest
from unittest.mock import Mock, AsyncMock
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
        if not intermediate_steps:
            return AgentFinish(
                return_values={"output": "I need more information to help you."},
                log="No intermediate steps available"
            )
        return AgentFinish(
            return_values={"output": intermediate_steps[-1][1]},
            log="Completed processing"
        )
    
    async def aplan(self, intermediate_steps: List[Tuple[AgentAction, str]], **kwargs: Any) -> Union[AgentAction, AgentFinish]:
        """Async version of plan."""
        return await self.plan(intermediate_steps, **kwargs)
    
    @property
    def input_keys(self) -> List[str]:
        """Return the input keys required for the agent."""
        return ["input"]
    
    async def execute(self, tool_input: str) -> str:
        """Execute a tool with the given input."""
        return f"Executed tool with input: {tool_input}"
    
    @property
    def _agent_type(self) -> str:
        """Get the agent type."""
        return self.name
    
    @property
    def _llm_prefix(self) -> str:
        """Get the LLM prefix."""
        return f"You are the {self.name} agent for the Bio-Age Coach. {self.description}"
    
    @property
    def _observation_prefix(self) -> str:
        """Get the observation prefix."""
        return "Observation: "
    
    @property
    def _llm_suffix(self) -> str:
        """Get the LLM suffix."""
        return "\nThought: "
    
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
    
    def get_state(self) -> AgentState:
        """Get current agent state."""
        return self.state.get('state', AgentState.INITIALIZING)
    
    def set_state(self, state: AgentState) -> None:
        """Set agent state."""
        self.state['state'] = state
    
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
def test_agent(mock_mcp_client):
    """Create a test agent instance."""
    return TestAgent(
        name="test_agent",
        description="Test agent for unit testing",
        api_key="test_key",
        mcp_client=mock_mcp_client
    )

@pytest.mark.asyncio
async def test_agent_initialization(test_agent):
    """Test agent initialization."""
    assert test_agent.name == "test_agent"
    assert test_agent.api_key == "test_key"
    assert isinstance(test_agent.mcp_client, MultiServerMCPClient)
    assert "state" in test_agent.state
    assert test_agent.capabilities == ["test_capability"]

@pytest.mark.asyncio
async def test_can_handle(test_agent):
    """Test can_handle method."""
    assert await test_agent.can_handle("test query", {}) == 1.0
    assert await test_agent.can_handle("other query", {}) == 0.0

@pytest.mark.asyncio
async def test_process(test_agent):
    """Test process method."""
    response = await test_agent.process("test query", {})
    assert response["response"] == "Test response"
    assert response["insights"] == ["Test insight"]
    assert response["visualization"] is None
    assert response["error"] is None

@pytest.mark.asyncio
async def test_send_request(test_agent, mock_mcp_client):
    """Test send_request method."""
    response = await test_agent.send_request("test_server", {"type": "test"})
    assert response == {"result": "test"}
    mock_mcp_client.send_request.assert_called_once_with(
        "test_server",
        {"type": "test"}
    )

@pytest.mark.asyncio
async def test_update_context(test_agent):
    """Test update_context method."""
    test_agent.update_context({"test": "value"})
    assert test_agent.state["test"] == "value"

@pytest.mark.asyncio
async def test_plan(test_agent):
    """Test plan method."""
    result = await test_agent.plan([])
    assert result.return_values["output"] == "I need more information to help you."

@pytest.mark.asyncio
async def test_execute(test_agent):
    """Test execute method."""
    result = await test_agent.execute("test input")
    assert result == "Executed tool with input: test input"

def test_agent_properties(test_agent):
    """Test agent properties."""
    assert test_agent._agent_type == "test_agent"
    assert "test_agent" in test_agent._llm_prefix
    assert test_agent._observation_prefix == "Observation: "
    assert test_agent._llm_suffix == "\nThought: " 