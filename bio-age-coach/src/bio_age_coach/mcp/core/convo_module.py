"""
Base template for conversation modules in the Bio Age Coach system.
Each module manages a specific health topic and can interact with multiple MCP servers
to provide comprehensive functionality.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Set
from dataclasses import dataclass
from enum import Enum
from ..utils.client import MultiServerMCPClient

class ConvoState(Enum):
    """States in the conversation lifecycle."""
    COLLECT_DATA = "collect_data"
    LEARN_HABITS = "learn_habits"
    MAKE_RECOMMENDATIONS = "make_recommendations"
    ANSWER_QUESTIONS = "answer_questions"
    SELECT_RECOMMENDATIONS = "select_recommendations"

@dataclass
class Resource:
    """Definition of a resource available to the module.
    Resources can be distributed across different servers based on functionality."""
    name: str
    type: str
    access_path: str
    description: str
    server_type: str  # The type of server this resource belongs to

@dataclass
class Tool:
    """Definition of a tool available to the module.
    Tools can be distributed across different servers based on functionality."""
    name: str
    function: callable
    description: str
    parameters: Dict[str, Any]
    server_type: str  # The type of server this tool belongs to

class ConvoModule(ABC):
    """Base class for conversation modules.
    
    Each module:
    - Handles a specific health topic
    - Can interact with multiple servers for different functionalities
    - Maintains its own state and context
    - Coordinates responses across servers
    """
    
    def __init__(self, api_key: str, topic: str, mcp_client: MultiServerMCPClient):
        """Initialize the conversation module.
        
        Args:
            api_key: API key for external services
            topic: Health topic this module handles (e.g., "sleep", "exercise")
            mcp_client: MultiServerMCPClient instance for server communication
        """
        self.api_key = api_key
        self.topic = topic
        self.mcp_client = mcp_client
        self.state = ConvoState.COLLECT_DATA
        self.resources: Dict[str, Resource] = {}
        self.tools: Dict[str, Tool] = {}
        self.prompts: Dict[str, str] = {}
        self.server_types: Set[str] = set()  # Tracks all server types this module interacts with
        
        # Initialize module components
        self._initialize_resources()
        self._initialize_tools()
        self._initialize_prompts()
    
    @abstractmethod
    def _initialize_resources(self) -> None:
        """Initialize resources available to this module.
        Resources can be distributed across different servers based on functionality.
        """
        pass
    
    @abstractmethod
    def _initialize_tools(self) -> None:
        """Initialize tools available to this module.
        Tools can be distributed across different servers based on functionality.
        """
        pass
    
    @abstractmethod
    def _initialize_prompts(self) -> None:
        """Initialize conversation prompts for this module.
        Prompts should be designed to work across multiple servers when needed.
        """
        pass
    
    @abstractmethod
    async def _process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process a request in the current conversation state.
        
        This method should coordinate interactions across multiple servers
        to provide a comprehensive response.
        
        Args:
            request: The request to process, including:
                - action: The action to perform
                - user_id: The user making the request
                - query: The user's query (for process_query action)
                - context: Current conversation context
                - metadata: Additional request metadata
            
        Returns:
            Response data combining results from relevant servers
        """
        pass
    
    def add_resource(self, name: str, resource: Resource) -> None:
        """Add a resource to the module.
        
        Args:
            name: Resource identifier
            resource: Resource definition with server type
        """
        self.resources[name] = resource
        self.server_types.add(resource.server_type)
    
    def add_tool(self, name: str, tool: Tool) -> None:
        """Add a tool to the module.
        
        Args:
            name: Tool identifier
            tool: Tool definition with server type
        """
        self.tools[name] = tool
        self.server_types.add(tool.server_type)
    
    def add_prompt(self, name: str, prompt: str) -> None:
        """Add a conversation prompt to the module.
        
        Args:
            name: Prompt identifier
            prompt: Prompt template that may reference multiple servers
        """
        self.prompts[name] = prompt
    
    def get_state(self) -> ConvoState:
        """Get current conversation state."""
        return self.state
    
    def set_state(self, state: ConvoState) -> None:
        """Set conversation state.
        
        Args:
            state: New conversation state
        """
        self.state = state
    
    def get_resource(self, name: str) -> Optional[Resource]:
        """Get a resource by name.
        
        Args:
            name: Resource identifier
            
        Returns:
            Resource if found, None otherwise
        """
        return self.resources.get(name)
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """Get a tool by name.
        
        Args:
            name: Tool identifier
            
        Returns:
            Tool if found, None otherwise
        """
        return self.tools.get(name)
    
    def get_prompt(self, name: str) -> Optional[str]:
        """Get a prompt by name.
        
        Args:
            name: Prompt identifier
            
        Returns:
            Prompt template if found, None otherwise
        """
        return self.prompts.get(name)
    
    async def send_request(self, server_type: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send a request to a specific server through the MCP client.
        
        Args:
            server_type: Type of server to send request to
            request_data: Request data to send
            
        Returns:
            Response from the server
            
        Raises:
            ValueError: If server_type is not registered with this module
        """
        if server_type not in self.server_types:
            raise ValueError(f"Server type '{server_type}' not registered with module '{self.topic}'")
        
        return await self.mcp_client.send_request(server_type, request_data)
    
    async def close(self) -> None:
        """Clean up module resources."""
        pass  # Override if needed 