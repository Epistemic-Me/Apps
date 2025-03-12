"""Base MCP server implementation."""

from typing import Dict, Any
import asyncio
import logging
from abc import ABC, abstractmethod

class BaseMCPServer(ABC):
    """Base class for all MCP servers."""
    
    def __init__(self, api_key: str):
        """Initialize the base MCP server.
        
        Args:
            api_key (str): API key for authentication
        """
        self.api_key = api_key
        self.logger = logging.getLogger(self.__class__.__name__)
        
    async def authenticate(self, request: Dict[str, Any]) -> bool:
        """Authenticate an incoming request.
        
        Args:
            request (Dict[str, Any]): The incoming request
            
        Returns:
            bool: True if authentication succeeds, False otherwise
        """
        return request.get("api_key") == self.api_key
        
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle an incoming request.
        
        Args:
            request (Dict[str, Any]): The incoming request
            
        Returns:
            Dict[str, Any]: The response
        """
        try:
            if not await self.authenticate(request):
                return {"error": "Authentication failed"}
                
            self.logger.info(f"Processing request: {request.get('type', 'unknown')}")
            response = await self._process_request(request)
            self.logger.info("Request processed successfully")
            
            return response
        except Exception as e:
            self.logger.error(f"Error processing request: {str(e)}")
            return {"error": str(e)}
    
    @abstractmethod
    async def _process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process the request after authentication.
        
        This method must be implemented by subclasses.
        
        Args:
            request (Dict[str, Any]): The authenticated request
            
        Returns:
            Dict[str, Any]: The response
        """
        raise NotImplementedError
        
    async def initialize_data(self, data: Dict[str, Any]) -> None:
        """Initialize server with data. Must be implemented by subclasses."""
        raise NotImplementedError
        
    async def close(self) -> None:
        """Close any open connections."""
        pass 