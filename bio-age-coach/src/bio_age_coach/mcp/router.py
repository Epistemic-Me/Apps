"""
Query router implementation for routing requests to appropriate servers.
"""

from typing import Dict, Any, Optional
from .health_server import HealthServer
from .research_server import ResearchServer
from .tools_server import ToolsServer
from .bio_age_score_server import BioAgeScoreServer
import logging

class QueryRouter:
    """Router for directing queries to appropriate servers."""
    
    def __init__(self, health_server: HealthServer, research_server: ResearchServer, tools_server: ToolsServer, bio_age_score_server: BioAgeScoreServer):
        """Initialize the router with server instances."""
        self.health_server = health_server
        self.research_server = research_server
        self.tools_server = tools_server
        self.bio_age_score_server = bio_age_score_server
        self.logger = logging.getLogger(__name__)
        
    async def route_query(self, query: str) -> Dict[str, Any]:
        """Route a query to appropriate servers and aggregate responses."""
        query_lower = query.lower()
        
        # Initialize response dictionary
        responses = {
            "unknown": {
                "server": "unknown",
                "type": "error",
                "error": "Could not determine appropriate server for query"
            }
        }
        
        # Check query type flags
        is_research_query = any(term in query_lower for term in [
            "research", "study", "evidence", "paper", "publication"
        ])
        
        is_health_query = any(term in query_lower for term in [
            "health", "fitness", "workout", "exercise", "sleep", "diet"
        ])
        
        is_tools_query = any(term in query_lower for term in [
            "calculate", "measure", "analyze", "test", "metric"
        ])
        
        is_bio_age_query = any(term in query_lower for term in [
            "bio", "age", "biological", "longevity", "score", "trend"
        ])
        
        # Get research insights if it's a research query
        if is_research_query:
            self.logger.info("Processing research query")
            responses["research"] = {
                "server": "research",
                "type": "query",
                "data": {}
            }
            self.logger.info(f"Research response: {responses['research']}")
            
        # Get health data if it's a health query
        if is_health_query:
            self.logger.info("Processing health query")
            responses["health"] = {
                "server": "health",
                "type": "query",
                "data": {}
            }
            self.logger.info(f"Health response: {responses['health']}")
            
        # Get tools data if it's a tools query
        if is_tools_query:
            self.logger.info("Processing tools query")
            responses["tools"] = {
                "server": "tools",
                "type": "query",
                "data": {}
            }
            self.logger.info(f"Tools response: {responses['tools']}")
                    
        # Get bio age score insights if it's a bio age query
        if is_bio_age_query:
            self.logger.info("Processing bio age query")
            if "trend" in query_lower or "visualization" in query_lower or "chart" in query_lower or "graph" in query_lower or "show me" in query_lower or "display" in query_lower or "plot" in query_lower:
                responses["bio_age_score"] = {
                    "server": "bio_age_score",
                    "type": "visualization",
                    "data": {}
                }
            else:
                responses["bio_age_score"] = {
                    "server": "bio_age_score",
                    "type": "query",
                    "data": {}
                }
            self.logger.info(f"Bio age response: {responses['bio_age_score']}")
            
        # Return the most relevant response based on query priority
        if is_research_query and "research" in responses:
            self.logger.info("Returning research response")
            return responses["research"]
        elif is_bio_age_query and "bio_age_score" in responses:
            self.logger.info("Returning bio age score response")
            return responses["bio_age_score"]
        elif is_tools_query and "calculate" in query_lower and "trends" not in query_lower:
            self.logger.info("Returning tools response (calculate)")
            return responses.get("tools", responses["unknown"])
        elif is_health_query and "trends" in query_lower:
            self.logger.info("Returning health response (trends)")
            return responses.get("health", responses["unknown"])
        elif is_tools_query:
            self.logger.info("Returning tools response")
            return responses.get("tools", responses["unknown"])
        elif is_health_query:
            self.logger.info("Returning health response")
            return responses.get("health", responses["unknown"])
        else:
            self.logger.info("Returning unknown response")
            return responses["unknown"]

class RouterContext:
    """Context for routing MCP requests."""
    
    def __init__(
        self,
        tools_server: Optional[ToolsServer] = None,
        health_server: Optional[HealthServer] = None,
        bio_age_score_server: Optional[BioAgeScoreServer] = None
    ):
        """Initialize router context with available servers."""
        self.tools_server = tools_server
        self.health_server = health_server
        self.bio_age_score_server = bio_age_score_server

class MCPRouter:
    """Router for MCP requests."""
    
    def __init__(self, context: RouterContext):
        """Initialize router with context."""
        self.context = context
        self.routes = {
            "tools": self.context.tools_server,
            "health": self.context.health_server,
            "bio_age_score": self.context.bio_age_score_server
        }
    
    async def route(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route request to appropriate server.
        
        Args:
            request: Dictionary containing request details
                Required keys: server, action, params
                
        Returns:
            Response from server
        """
        server_name = request.get("server")
        if not server_name:
            raise ValueError("Server name not specified in request")
            
        server = self.routes.get(server_name)
        if not server:
            raise ValueError(f"Unknown server: {server_name}")
            
        action = request.get("action")
        if not action:
            raise ValueError("Action not specified in request")
            
        params = request.get("params", {})
        
        # Route to appropriate server method
        if hasattr(server, action):
            method = getattr(server, action)
            return await method(**params)
        else:
            raise ValueError(f"Unknown action {action} for server {server_name}")
            
    async def initialize(self) -> None:
        """Initialize all servers in router."""
        for server in self.routes.values():
            if server and hasattr(server, "initialize"):
                await server.initialize()
                
    async def shutdown(self) -> None:
        """Shutdown all servers in router."""
        for server in self.routes.values():
            if server and hasattr(server, "shutdown"):
                await server.shutdown() 