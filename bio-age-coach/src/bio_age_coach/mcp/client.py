"""
Client implementation for interacting with multiple MCP servers.
"""

import asyncio
from typing import Dict, Any, Optional, List
import aiohttp
from .health_server import HealthServer
from .research_server import ResearchServer
from .tools_server import ToolsServer
from .bio_age_score_server import BioAgeScoreServer

class MultiServerMCPClient:
    """Client for interacting with multiple MCP servers."""
    
    def __init__(
        self,
        health_server: Optional[HealthServer] = None,
        research_server: Optional[ResearchServer] = None,
        tools_server: Optional[ToolsServer] = None,
        bio_age_score_server: Optional[BioAgeScoreServer] = None
    ):
        """Initialize the client with server instances."""
        self.health_server = health_server
        self.research_server = research_server
        self.tools_server = tools_server
        self.bio_age_score_server = bio_age_score_server
        self.user_data = {}
        
    async def send_request(self, server_type: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send a request to the appropriate server based on type."""
        try:
            if server_type == "health" and self.health_server:
                # Handle health server requests
                request_type = request_data.get("type", "")
                if request_type == "user_data":
                    return await self.health_server.get_user_data(request_data.get("user_id", "test_user"))
                elif request_type == "update_data":
                    await self.health_server.update_user_data(request_data.get("user_id", "test_user"), request_data["data"])
                    return {"status": "success"}
                elif request_type == "users":
                    return await self.health_server.get_users()
                elif request_type == "query":
                    return await self.health_server._process_request(request_data)
                
            elif server_type == "research" and self.research_server:
                # Handle research server requests
                request_type = request_data.get("type", "")
                if request_type == "get_papers":
                    return await self.research_server.get_papers(request_data.get("query", ""))
                elif request_type == "get_insights":
                    return await self.research_server.get_insights(request_data.get("query", ""))
                elif request_type == "query":
                    return await self.research_server._process_request(request_data)
                
            elif server_type == "tools" and self.tools_server:
                # Handle tools server requests
                request_type = request_data.get("type", "")
                if request_type == "get_config":
                    return await self.tools_server.get_config()
                elif request_type == "run_tool":
                    return await self.tools_server.run_tool(request_data["tool_name"], request_data["params"])
                elif request_type == "query":
                    return await self.tools_server._process_request(request_data)
                
            elif server_type == "bio_age_score" and self.bio_age_score_server:
                # Handle bio age score server requests
                request_type = request_data.get("type", "")
                if request_type == "calculate_daily_score":
                    return await self.bio_age_score_server.calculate_daily_score(request_data.get("data", {}))
                elif request_type == "calculate_30_day_scores":
                    health_data = request_data.get("data", {}).get("health_data", [])
                    if isinstance(health_data, list):
                        scores = await self.bio_age_score_server.calculate_30_day_scores(health_data)
                        if scores:
                            # Add trend analysis
                            trend_data = scores[-1] if isinstance(scores[-1], dict) and "trend_analysis" in scores[-1] else {}
                            return {
                                "scores": scores[:-1] if trend_data else scores,
                                "trends": trend_data.get("trend_analysis", {})
                            }
                    return {"scores": [], "trends": {}}
                elif request_type == "visualization":
                    health_data = request_data.get("data", {}).get("health_data", [])
                    if isinstance(health_data, list):
                        scores = await self.bio_age_score_server.calculate_30_day_scores(health_data)
                        if scores:
                            viz_response = await self.bio_age_score_server.create_score_visualization(scores[:-1] if isinstance(scores[-1], dict) and "trend_analysis" in scores[-1] else scores)
                            if isinstance(viz_response, dict) and "visualization" in viz_response:
                                viz_data = viz_response["visualization"]
                                return {
                                    "visualization": {
                                        "dates": viz_data.get("dates", []),
                                        "scores": viz_data.get("scores", []),
                                        "reference_ranges": viz_data.get("reference_ranges", {})
                                    },
                                    "insights": viz_response.get("insights", [])
                                }
                    return {"error": "Failed to create visualization"}
                elif request_type == "store_habits":
                    await self.bio_age_score_server.store_habits_beliefs(
                        request_data["user_id"],
                        request_data["habits"]
                    )
                    return {"status": "success"}
                elif request_type == "store_plan":
                    await self.bio_age_score_server.store_user_plan(
                        request_data["user_id"],
                        request_data["plan"]
                    )
                    return {"status": "success"}
                elif request_type == "get_habits":
                    habits = await self.bio_age_score_server.get_habits_beliefs(request_data["user_id"])
                    return {"habits": habits} if habits else {"error": "No habits found"}
                elif request_type == "get_plan":
                    plan = await self.bio_age_score_server.get_user_plan(request_data["user_id"])
                    return {"plan": plan} if plan else {"error": "No plan found"}
                elif request_type == "query":
                    return await self.bio_age_score_server._process_request(request_data)
            return {"error": "Invalid server type or request"}
        except Exception as e:
            print(f"Error sending request: {str(e)}")
            return {"error": f"Request failed: {str(e)}"}
        
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
                return {
                    "visualization": viz_data.get("figure", {}),
                    "reference_ranges": viz_data.get("reference_ranges", {}),
                    "insights": viz_data.get("insights", [])
                }
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
        
    async def close(self) -> None:
        """Close all server connections."""
        if self.health_server:
            await self.health_server.close()
        if self.research_server:
            await self.research_server.close()
        if self.tools_server:
            await self.tools_server.close()
        if self.bio_age_score_server:
            await self.bio_age_score_server.close() 