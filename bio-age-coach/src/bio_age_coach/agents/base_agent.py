"""
Base template for agents in the Bio Age Coach system.
Each agent handles a specific health topic and can interact with multiple MCP servers
to provide specialized functionality within the multi-agent architecture.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Set, List, Tuple, Union
from enum import Enum
from langchain.agents.agent import AgentExecutor
from langchain.schema import AgentAction, AgentFinish
from langchain.callbacks.manager import CallbackManagerForChainRun
from langchain.tools import BaseTool
from bio_age_coach.mcp.client import MultiServerMCPClient
from ..router.observation_context import ObservationContext, SleepObservationContext, ExerciseObservationContext

class AgentState(Enum):
    """States in the agent operation lifecycle."""
    INITIALIZING = "initializing"
    READY = "ready"
    PROCESSING = "processing"
    WAITING = "waiting"
    ERROR = "error"

class Agent(ABC):
    """Base class for all Bio-Age Coach agents.
    
    This class provides a foundation for specialized agents in the Bio Age Coach system.
    It uses composition with LangChain's AgentExecutor when needed, rather than inheritance,
    to avoid Pydantic compatibility issues while still leveraging LangChain's capabilities.
    """
    
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
            **kwargs: Additional arguments for configuration
        """
        # Set agent attributes
        self.name = name
        self.description = description
        self.api_key = api_key
        self.mcp_client = mcp_client
        self.tools = tools or []
        self.state = AgentState.INITIALIZING
        self.capabilities: List[str] = []
        self.server_types: Set[str] = set()  # Tracks all server types this agent interacts with
        self.domain_examples: List[str] = []  # Examples of queries this agent can handle
        self.supported_data_types: Set[str] = set()  # Data types this agent can process
        self.context: Dict[str, Any] = {}
        
        # Create a LangChain AgentExecutor if needed
        self.agent_executor = None
        if kwargs.get('use_langchain_executor', False) and tools:
            from langchain.agents import initialize_agent, AgentType
            from langchain.chat_models import ChatOpenAI
            
            llm = ChatOpenAI(
                temperature=kwargs.get('temperature', 0.7),
                model_name=kwargs.get('model_name', 'gpt-4o-mini'),
                openai_api_key=api_key
            )
            
            self.agent_executor = initialize_agent(
                tools=tools,
                llm=llm,
                agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
                verbose=kwargs.get('verbose', False)
            )
        
        # Initialize agent capabilities
        self._initialize_capabilities()
        self._initialize_servers()
        self._initialize_domain_examples()
        self._initialize_supported_data_types()
        self.state = AgentState.READY
    
    @abstractmethod
    def _initialize_capabilities(self) -> None:
        """Initialize the capabilities of this agent.
        Each capability represents a specific task the agent can perform.
        """
        pass
    
    @abstractmethod
    def _initialize_servers(self) -> None:
        """Initialize server types this agent will communicate with."""
        pass
    
    def _initialize_domain_examples(self) -> None:
        """Initialize examples of queries this agent can handle.
        
        This method can be overridden by specific agents to provide
        more detailed examples for semantic routing.
        """
        # Default implementation uses capabilities as examples
        self.domain_examples = self.capabilities.copy()
    
    def _initialize_supported_data_types(self) -> None:
        """Initialize data types this agent can process.
        
        This method can be overridden by specific agents to specify
        which data types they can process.
        """
        # Default implementation supports no data types
        self.supported_data_types = set()
    
    @abstractmethod
    async def can_handle(self, query: str, context: Dict[str, Any]) -> float:
        """Return confidence score for handling query (0-1).
        
        Args:
            query: User query
            context: Conversation context
            
        Returns:
            float: Confidence score between 0 and 1
        """
        pass
    
    @abstractmethod
    async def process(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process a query and return response.
        
        Args:
            query: User query
            context: Conversation context
            
        Returns:
            Dict[str, Any]: Response containing:
                - response: str - Main response text
                - insights: List[str] - Key insights
                - visualization: Optional[Dict] - Visualization data
                - error: Optional[str] - Error message if any
        """
        # Update the agent's context
        self.context.update(context)
        
        # If we have a LangChain agent executor, use it
        if self.agent_executor:
            try:
                # Prepare chat history for the agent
                chat_history = context.get("chat_history", [])
                
                # Run the LangChain agent
                result = await self.run_langchain_agent(query, chat_history)
                
                # Format the response
                return {
                    "response": result,
                    "insights": self._extract_insights(result),
                    "visualization": None,
                    "error": None
                }
            except Exception as e:
                # Fall back to the agent's own implementation
                pass
        
        # If no executor or it failed, use the agent's own implementation
        plan = await self.plan(query, context)
        return await self.execute(plan)
    
    async def run_langchain_agent(self, query: str, chat_history: List[str] = None) -> str:
        """Run the LangChain agent executor with the given query.
        
        Args:
            query: User query
            chat_history: Optional chat history
            
        Returns:
            str: Agent response
            
        Raises:
            ValueError: If agent_executor is not initialized
        """
        if not self.agent_executor:
            raise ValueError("LangChain agent executor not initialized")
        
        # Prepare inputs for the agent
        inputs = {
            "input": query,
            "chat_history": chat_history or []
        }
        
        # Run the agent
        result = await self.agent_executor.arun(inputs)
        return result
    
    def _extract_insights(self, text: str) -> List[str]:
        """Extract insights from the agent's response.
        
        Args:
            text: Response text
            
        Returns:
            List[str]: Extracted insights
        """
        # Simple implementation - look for bullet points or numbered lists
        insights = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            # Check for bullet points or numbered lists
            if line.startswith('- ') or line.startswith('* ') or (len(line) > 2 and line[0].isdigit() and line[1] == '.'):
                # Remove the bullet point or number
                if line.startswith('- ') or line.startswith('* '):
                    insight = line[2:].strip()
                else:
                    # Find the first dot and take everything after it
                    dot_index = line.find('.')
                    if dot_index != -1:
                        insight = line[dot_index + 1:].strip()
                    else:
                        insight = line
                
                if insight:
                    insights.append(insight)
        
        return insights
    
    async def create_observation_context(self, data_type: str, user_id: Optional[str] = None) -> Optional[ObservationContext]:
        """Create an observation context for the given data type.
        
        This method can be overridden by specific agents to create
        specialized observation contexts for different data types.
        
        Args:
            data_type: Type of data to create context for
            user_id: Optional user ID
            
        Returns:
            Optional[ObservationContext]: Observation context or None if not supported
        """
        # Check if this agent supports this data type
        if data_type not in self.supported_data_types:
            return None
            
        # Create appropriate observation context based on data type
        if data_type == "sleep":
            return SleepObservationContext(agent_name=self.name, user_id=user_id)
        elif data_type == "exercise":
            return ExerciseObservationContext(agent_name=self.name, user_id=user_id)
        else:
            # Create a generic observation context
            return ObservationContext(agent_name=self.name, data_type=data_type, user_id=user_id)
    
    async def plan(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Plan a response to the query.
        
        Args:
            query: User query
            context: Conversation context
            
        Returns:
            Dict[str, Any]: Planned response
        """
        # Default implementation - should be overridden by specific agents
        return {
            "response": "I need more information to help you.",
            "insights": [],
            "visualization": None,
            "error": None
        }
    
    async def execute(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a plan and return the result.
        
        Args:
            plan: The plan to execute
            
        Returns:
            Dict[str, Any]: Result of executing the plan
        """
        # Default implementation - should be overridden by specific agents
        return plan
    
    @property
    def input_keys(self) -> List[str]:
        """Return the input keys required for the agent.
        
        Returns:
            List[str]: List of input keys
        """
        return ["query", "context"]
    
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
        """Send a request to a specific server through the MCP client.
        
        Args:
            server_type: Type of server to send request to
            request_data: Request data to send
            
        Returns:
            Response from the server
            
        Raises:
            ValueError: If server_type is not registered with this agent
        """
        if server_type not in self.server_types:
            raise ValueError(f"Server type '{server_type}' not registered with agent '{self.name}'")
        
        return await self.mcp_client.send_request(server_type, request_data)
    
    def update_context(self, context_updates: Dict[str, Any]) -> None:
        """Update this agent's context with new information.
        
        Args:
            context_updates: New context information to merge with existing context
        """
        self.context.update(context_updates)
    
    def get_capabilities(self) -> List[str]:
        """Get the list of capabilities this agent provides.
        
        Returns:
            List of capability descriptions
        """
        return self.capabilities.copy()
    
    async def initialize_data(self, data: Dict[str, Any]) -> None:
        """Initialize the agent with data.
        
        Args:
            data: Initialization data
        """
        # Default implementation does nothing
        pass
    
    def get_state(self) -> AgentState:
        """Get current agent state."""
        return self.state
    
    def set_state(self, state: AgentState) -> None:
        """Set agent state.
        
        Args:
            state: New agent state
        """
        self.state = state
    
    async def close(self) -> None:
        """Clean up agent resources."""
        pass  # Override if needed 