"""
Registry for conversation modules.
"""

from typing import Dict, Any, Optional, Type, List
from .protocols import MCPServer
from .convo_module import ConvoModule, ConvoState
from ..modules.bio_age_score_module import BioAgeScoreModule
from ..utils.client import MultiServerMCPClient
import os

class ModuleRegistry:
    """Registry for managing conversation modules."""
    
    def __init__(self, mcp_client: Optional[MultiServerMCPClient] = None):
        """Initialize the module registry."""
        self.modules: Dict[str, Type[ConvoModule]] = {}
        self.mcp_client = mcp_client
        self._register_default_modules()
        
    def register_module(self, topic: str, module_class: Type[ConvoModule]) -> None:
        """Register a module class for a topic."""
        self.modules[topic] = module_class
        
    def get_module(self, topic: str) -> Optional[ConvoModule]:
        """Get a module instance by topic."""
        if topic not in self.modules:
            return None
        return self.create_module(topic)
        
    def list_modules(self) -> Dict[str, Type[ConvoModule]]:
        """List all registered modules."""
        return self.modules.copy()

    def _register_default_modules(self) -> None:
        """Register default conversation module classes."""
        # Import modules here to avoid circular imports
        from ..modules.bio_age_score_module import BioAgeScoreModule
        
        self.register_module("bio_age_score", BioAgeScoreModule)
    
    def create_module(self, topic: str) -> ConvoModule:
        """Create a new instance of a registered module.
        
        Args:
            topic: The health topic to create a module for
            
        Returns:
            A new instance of the conversation module
            
        Raises:
            KeyError: If no module class exists for the topic
        """
        if topic not in self.modules:
            raise KeyError(f"No conversation module class registered for topic: {topic}")
        
        module_class = self.modules[topic]
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        return module_class(api_key, self.mcp_client)
    
    def get_module_state(self, topic: str) -> Optional[ConvoState]:
        """Get the current state of a module if it exists.
        
        Args:
            topic: The health topic to get state for
            
        Returns:
            The module's current state, or None if module doesn't exist
        """
        module = self.get_module(topic)
        return module.get_state() if module else None
    
    async def route_request(self, topic: str, request: Dict[str, Any]) -> Dict[str, Any]:
        """Route a request to the appropriate module.
        
        Args:
            topic: The health topic to route to
            request: The request to process
            
        Returns:
            The response from the module
        """
        module_class = self.get_module(topic)
        return await module_class._process_request(request)
    
    def list_topics(self) -> List[str]:
        """List all registered module topics.
        
        Returns:
            List of registered topic names
        """
        return list(self.modules.keys())
    
    def list_active_modules(self) -> List[str]:
        """List topics of currently active module instances.
        
        Returns:
            List of active module topic names
        """
        return list(self.modules.keys())
    
    async def close(self) -> None:
        """Close all active module instances."""
        for module_class in self.modules.values():
            await module_class.close() 