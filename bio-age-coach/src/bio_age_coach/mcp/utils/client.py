"""
Client for managing multiple MCP servers.
"""

import asyncio
from typing import Dict, Any, Optional, List
import aiohttp
import logging
from ..servers.health_server import HealthServer
from ..servers.research_server import ResearchServer
from ..servers.tools_server import ToolsServer
from ..servers.bio_age_score_server import BioAgeScoreServer
from ..core.protocols import MCPServer

class MultiServerMCPClient:
    """Client for interacting with multiple MCP servers."""
    
    def __init__(self):
        """Initialize the client."""
        self.servers: Dict[str, MCPServer] = {}
        self.health_server = None
        self.research_server = None
        self.tools_server = None
        self.bio_age_score_server = None
        self.user_data = {}
    
    def register_server(self, server_type: str, server: MCPServer) -> None:
        """Register a server instance.
        
        Args:
            server_type: Type identifier for the server
            server: Server instance implementing MCPServer protocol
        """
        self.servers[server_type] = server
        
        # Set instance variables based on server type
        if server_type == "health":
            self.health_server = server
        elif server_type == "research":
            self.research_server = server
        elif server_type == "tools":
            self.tools_server = server
        elif server_type == "bio_age_score":
            self.bio_age_score_server = server
    
    def get_server(self, server_type: str) -> Optional[MCPServer]:
        """Get a registered server by type.
        
        Args:
            server_type: Type identifier for the server
            
        Returns:
            Server instance if registered, None otherwise
        """
        return self.servers.get(server_type)
    
    async def send_request(self, server_type: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send a request to the appropriate server based on type.
        
        Args:
            server_type: Type of server to send request to
            request_data: Request data to send
            
        Returns:
            Response from the server
            
        Raises:
            ValueError: If server_type is not registered
        """
        server = self.get_server(server_type)
        if not server:
            raise ValueError(f"No server registered for type: {server_type}")
        
        try:
            return await server.process_request(request_data)
        except Exception as e:
            logging.error(f"Error processing request for server {server_type}: {e}")
            return {"error": f"Request failed: {str(e)}"}
    
    async def close(self) -> None:
        """Close all server connections."""
        for server in self.servers.values():
            await server.close()
        
    async def get_health_data(self, user_id: str) -> Dict[str, Any]:
        """Get health data for a user."""
        if self.health_server:
            data = await self.health_server.get_user_data(user_id)
            self.user_data[user_id] = data
            return data
        return {}
        
    async def update_health_data(self, user_id: str, data: Dict[str, Any]) -> None:
        """Update health data for a user."""
        if self.health_server:
            await self.health_server.update_user_data(user_id, data)
            self.user_data[user_id] = data
        
    async def get_research_insights(self, query: str) -> List[Dict[str, Any]]:
        """Get research insights based on a query."""
        if self.research_server:
            return await self.research_server.get_insights(query)
        return []
        
    async def get_tool_results(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get results from a specific tool."""
        if self.tools_server:
            return await self.tools_server.run_tool(tool_name, params)
        return {}
        
    async def get_bio_age_score(self, health_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate bio age score from health data."""
        if self.bio_age_score_server:
            score_data = await self.bio_age_score_server.calculate_daily_score(health_data)
            return {
                "score": score_data.get("total_score", 0),
                "breakdown": {
                    "sleep": score_data.get("sleep_score", 0),
                    "exercise": score_data.get("exercise_score", 0),
                    "steps": score_data.get("steps_score", 0)
                },
                "insights": score_data.get("insights", [])
            }
        return {}
        
    async def get_30_day_scores(self, health_data_series: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Calculate bio age scores for 30 days."""
        if self.bio_age_score_server:
            scores = await self.bio_age_score_server.calculate_30_day_scores(health_data_series)
            if scores:
                # Extract trend analysis
                trend_data = scores[-1] if isinstance(scores[-1], dict) and "trend_analysis" in scores[-1] else {}
                return {
                    "scores": scores[:-1] if trend_data else scores,
                    "trends": trend_data.get("trend_analysis", {}),
                    "summary": {
                        "average_score": sum(s.get("total_score", 0) for s in scores[:-1]) / len(scores[:-1]),
                        "best_score": max(s.get("total_score", 0) for s in scores[:-1]),
                        "worst_score": min(s.get("total_score", 0) for s in scores[:-1])
                    }
                }
        return {"scores": [], "trends": {}, "summary": {}}
        
    async def create_score_visualization(self, scores: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create visualization of bio age scores."""
        if self.bio_age_score_server:
            viz_data = await self.bio_age_score_server.create_score_visualization(scores)
            if isinstance(viz_data, dict):
                return viz_data
        return {}
        
    async def store_habits_beliefs(self, user_id: str, habits: Dict[str, Any]) -> None:
        """Store user's habits and beliefs."""
        if self.bio_age_score_server:
            await self.bio_age_score_server.store_habits_beliefs(user_id, habits)
        
    async def store_user_plan(self, user_id: str, plan: Dict[str, Any]) -> None:
        """Store user's improvement plan."""
        if self.bio_age_score_server:
            await self.bio_age_score_server.store_user_plan(user_id, plan)
        
    async def get_habits_beliefs(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user's stored habits and beliefs."""
        if self.bio_age_score_server:
            habits = await self.bio_age_score_server.get_habits_beliefs(user_id)
            if habits:
                return {
                    "habits": habits,
                    "timestamp": habits.get("timestamp", "")
                }
        return None
        
    async def get_user_plan(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user's stored improvement plan."""
        if self.bio_age_score_server:
            plan = await self.bio_age_score_server.get_user_plan(user_id)
            if plan:
                return {
                    "plan": plan,
                    "timestamp": plan.get("timestamp", "")
                }
        return None 