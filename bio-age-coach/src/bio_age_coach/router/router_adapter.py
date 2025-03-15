"""Router adapter for the Bio Age Coach system.

This module provides an adapter that wraps the SemanticRouter to maintain
compatibility with the existing QueryRouter interface.
"""

from typing import Dict, Any, List, Optional
import asyncio
import logging

from bio_age_coach.router.semantic_router import SemanticRouter
from bio_age_coach.mcp.client import MultiServerMCPClient
from bio_age_coach.mcp.core.module_registry import ModuleRegistry
from bio_age_coach.mcp.core.router import QueryRouter

logger = logging.getLogger(__name__)

class RouterAdapter(QueryRouter):
    """Adapter for the SemanticRouter to maintain compatibility with QueryRouter interface."""
    
    def __init__(self, semantic_router: SemanticRouter, mcp_client: Optional[MultiServerMCPClient] = None, module_registry: Optional[ModuleRegistry] = None):
        """Initialize the router adapter.
        
        Args:
            semantic_router: The semantic router to adapt
            mcp_client: Optional MCP client for backward compatibility
            module_registry: Optional module registry for backward compatibility
        """
        # Create a default module registry if none is provided
        if module_registry is None:
            module_registry = ModuleRegistry()
            
        # Create a default MCP client if none is provided
        if mcp_client is None:
            mcp_client = MultiServerMCPClient(api_key="test_key")
            
        # Initialize the base class with required parameters
        super().__init__(mcp_client=mcp_client, module_registry=module_registry)
        
        self.semantic_router = semantic_router
        self.mcp_client = mcp_client
        self.context = {}
    
    async def route_query(self, user_id: str, query: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Route a query to the appropriate agent.
        
        Args:
            user_id: The user ID
            query: The user query
            metadata: Optional metadata for the query
            
        Returns:
            Dict[str, Any]: The response from the agent
        """
        # Route the query using the semantic router
        response = await self.semantic_router.route_query(
            user_id=user_id,
            query=query,
            metadata=metadata
        )
        
        # Format the response to match QueryRouter interface
        formatted_response = self._format_response(response)
        
        return formatted_response
    
    def _format_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Format the response to match QueryRouter interface.
        
        Args:
            response: The response from the semantic router
            
        Returns:
            Dict[str, Any]: The formatted response
        """
        formatted_response = {
            "response": response.get("response", ""),
            "error": response.get("error"),
            "visualization": response.get("visualization"),
            "insights": response.get("insights", []),
            "recommendations": response.get("recommendations", []),
            "questions": response.get("questions", []),
            "agent_responses": response.get("agent_responses", []),
            "metrics": response.get("metrics", {}),
            "total_score": response.get("total_score", 0)
        }
        
        return formatted_response
    
    def update_context(self, user_id: str, context_update: Dict[str, Any]) -> None:
        """Update the context for a user.
        
        Args:
            user_id: The user ID
            context_update: The context update
        """
        if user_id not in self.context:
            self.context[user_id] = {}
        
        self.context[user_id].update(context_update)
        
        # Also update the semantic router's context
        self.semantic_router.update_context(user_id, context_update)
    
    def clear_context(self, user_id: str) -> None:
        """Clear the context for a user.
        
        Args:
            user_id: The user ID
        """
        if user_id in self.context:
            del self.context[user_id]
        
        # Also clear the semantic router's context
        self.semantic_router.clear_context(user_id)
    
    def get_active_topic(self, user_id: str) -> str:
        """Get the active topic for a user.
        
        Args:
            user_id: The user ID
            
        Returns:
            str: The active topic
        """
        return self.semantic_router.get_active_topic(user_id)
    
    async def handle_data_upload(self, user_id: str, data_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a data upload.
        
        Args:
            user_id: The user ID
            data_type: The type of data being uploaded
            data: The data being uploaded
            
        Returns:
            Dict[str, Any]: The response from processing the data
        """
        metadata = {
            "data_upload": True,
            "data_type": data_type,
            "data": data
        }
        
        # Route a generic query to trigger data processing
        query = f"I've uploaded new {data_type} data. What insights can you provide?"
        
        response = await self.semantic_router.route_query(
            user_id=user_id,
            query=query,
            metadata=metadata
        )
        
        # Format the response to match QueryRouter interface
        formatted_response = self._format_response(response)
        
        return formatted_response 