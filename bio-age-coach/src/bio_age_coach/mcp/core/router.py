"""
Context-aware router for the Bio Age Coach system.
Routes user queries to the appropriate conversation module based on context.
Each route maps to exactly one module, though modules may interact with multiple servers.
"""

from typing import Dict, Any, Optional, Set
import logging
import re
from .module_registry import ModuleRegistry
from .convo_module import ConvoState
from ..utils.client import MultiServerMCPClient

class QueryRouter:
    """Routes queries to the appropriate conversation module based on context."""
    
    def __init__(self, mcp_client: MultiServerMCPClient, module_registry: Optional[ModuleRegistry] = None):
        """Initialize the query router.
        
        Args:
            mcp_client: Client for interacting with MCP servers
            module_registry: Registry of available conversation modules
        """
        self.mcp_client = mcp_client
        self.module_registry = module_registry or ModuleRegistry(mcp_client)
        self.context: Dict[str, Any] = {}
        self.active_topic: Optional[str] = None
        
        # Define core intents and their associated servers
        self.intents = {
            "health_analysis": {
                "servers": ["health", "bio_age_score"],
                "keywords": [
                    "health metrics", "analyze health", "health data", "health profile",
                    "health information", "my health", "health analysis", "health date",
                    "health stats", "health status", "health summary", "health details",
                    "show health", "display health", "get health", "tell me about health"
                ],
                "timeframe_keywords": ["last", "days", "weeks", "months"]
            },
            "bio_age": {
                "servers": ["bio_age_score"],
                "keywords": [
                    "bio age score", "biological age", "bioage", "calculate score",
                    "bio age", "biological", "my score", "tell me about bio age",
                    "what's my bio age", "show bio age", "display bio age"
                ],
                "timeframe_keywords": ["last", "days", "weeks", "months"]
            },
            "research": {
                "servers": ["research"],
                "keywords": ["research", "evidence", "studies", "scientific", "findings"],
                "timeframe_keywords": []
            },
            "visualization": {
                "servers": ["bio_age_score"],
                "keywords": ["graph", "chart", "visualize", "plot", "trend", "show trends"],
                "timeframe_keywords": ["last", "days", "weeks", "months"]
            }
        }
    
    def _identify_intent(self, query: str) -> str:
        """Identify the primary intent of the query."""
        query = query.lower()
        
        # Score each intent based on keyword matches
        intent_scores = {}
        for intent, config in self.intents.items():
            score = 0
            # Check for exact keyword matches
            for keyword in config["keywords"]:
                keyword = keyword.lower()
                if keyword in query:
                    # Give higher weight to longer keyword matches
                    score += len(keyword.split()) * 2  # Double weight for exact matches
                # Also check for partial matches of multi-word keywords
                elif len(keyword.split()) > 1:
                    if all(word in query for word in keyword.split()):
                        score += len(keyword.split())
            
            # Special handling for research intent
            if intent == "research":
                research_terms = ["research", "evidence", "studies", "scientific", "findings"]
                if any(term in query for term in research_terms):
                    score += 5  # Give extra weight to research terms
            
            # Special handling for visualization intent
            if intent == "visualization":
                viz_terms = ["graph", "chart", "visualize", "plot", "trend"]
                if any(term in query for term in viz_terms):
                    score += 5  # Give extra weight to visualization terms
                    
            intent_scores[intent] = score
        
        # Return the intent with the highest score, or "unknown" if no matches
        if intent_scores:
            max_score = max(intent_scores.values())
            if max_score > 0:
                # If there's a tie, prioritize more specific intents
                max_intents = [i for i, s in intent_scores.items() if s == max_score]
                if len(max_intents) > 1:
                    priority = ["visualization", "research", "bio_age", "health_analysis"]
                    for p in priority:
                        if p in max_intents:
                            return p
                return max_intents[0]
        return "unknown"
    
    def _extract_timeframe(self, query: str) -> str:
        """Extract timeframe from query if present, otherwise return default."""
        query = query.lower()
        
        # Define regex patterns for different timeframe formats
        patterns = {
            'days': r'(?:last\s+)?(\d+)\s*(?:day|days|d)',
            'weeks': r'(?:last\s+)?(\d+)\s*(?:week|weeks|w)',
            'months': r'(?:last\s+)?(\d+)\s*(?:month|months|m)'
        }
        
        # Try to match each pattern
        for unit, pattern in patterns.items():
            match = re.search(pattern, query)
            if match:
                number = int(match.group(1))
                if unit == 'weeks':
                    number *= 7
                elif unit == 'months':
                    number *= 30
                return f"{number}D"
        
        # Default to 30 days if no timeframe specified
        return "30D"
    
    async def route_query(self, user_id: str, query: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Route a query to the appropriate server based on intent.
        
        Args:
            user_id: The user's ID
            query: The user's query
            metadata: Optional metadata for the query
            
        Returns:
            Dict containing the response and any updated context
        """
        # Update context with new query
        self._update_context(user_id, query, metadata)
        
        # Identify intent and timeframe
        intent = self._identify_intent(query)
        timeframe = self._extract_timeframe(query)
        
        if intent == "unknown":
            return {
                "error": "I'm not sure how to help with that. Try rephrasing your question.",
                "context": self.context
            }
        
        # Get the appropriate servers for the intent
        servers = self.intents[intent]["servers"]
        
        try:
            # First get health data if needed
            health_data = None
            if "health" in servers:
                health_response = await self.mcp_client.send_request("health", {
                    "type": "metrics",
                    "timeframe": timeframe,
                    "include_analysis": True
                })
                if isinstance(health_response, dict):
                    if "error" in health_response:
                        return {
                            "error": health_response["error"],
                            "context": self.context
                        }
                    health_data = health_response.get("metrics", {})
                    
                    # If this is a health analysis request and we have data, return it
                    if intent == "health_analysis" and health_data:
                        return {
                            "response": "Here's your health data analysis",
                            "metrics": health_data,
                            "insights": health_response.get("insights", []),
                            "context": self.context
                        }
            
            # Process with bio age score server if needed
            if "bio_age_score" in servers:
                if not health_data:
                    return {
                        "error": "I don't have any health data to calculate your bio-age score. Please upload your health data first.",
                        "context": self.context
                    }
                    
                bio_age_request = {
                    "type": "calculate_daily_score" if intent == "bio_age" else "create_visualization",
                    "metrics": {"health_data": health_data} if health_data else None,
                    "timeframe": timeframe
                }
                
                bio_age_response = await self.mcp_client.send_request("bio_age_score", bio_age_request)
                if isinstance(bio_age_response, dict):
                    if "error" in bio_age_response:
                        return {
                            "error": bio_age_response["error"],
                            "context": self.context
                        }
                    return {
                        "response": "Here's your health analysis",
                        "metrics": health_data,
                        "visualization": bio_age_response.get("visualization", {}),
                        "insights": bio_age_response.get("insights", []),
                        "context": self.context
                    }
            
            # Process with research server if needed
            if "research" in servers:
                research_response = await self.mcp_client.send_request("research", {
                    "type": "get_insights",
                    "query": query
                })
                if isinstance(research_response, dict):
                    if "error" in research_response:
                        return {
                            "error": research_response["error"],
                            "context": self.context
                        }
                    return {
                        "response": "Here's what I found from research",
                        "insights": research_response.get("insights", []),
                        "context": self.context
                    }
            
            return {
                "error": "I encountered an error processing your request. Please try again.",
                "context": self.context
            }
            
        except Exception as e:
            logging.error(f"Error processing query with intent {intent}: {e}")
            return {
                "error": str(e),
                "context": self.context
            }
    
    def _update_context(self, user_id: str, query: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Update conversation context with new query."""
        if user_id not in self.context:
            self.context[user_id] = {
                "queries": [],
                "active_topic": None,
                "module_state": None,
                "metadata": {}
            }
        
        user_context = self.context[user_id]
        user_context["queries"].append({
            "text": query,
            "metadata": metadata or {}
        })
        
        # Keep only last 10 queries for context
        if len(user_context["queries"]) > 10:
            user_context["queries"] = user_context["queries"][-10:]
        
        # Update metadata
        if metadata:
            user_context["metadata"].update(metadata)
    
    def _get_module_context(self, topic: str) -> Dict[str, Any]:
        """Get context relevant to the module."""
        return {
            "state": self.module_registry.get_module_state(topic),
            "active_topic": self.active_topic,
            "is_active": topic == self.active_topic
        }
    
    def get_active_topic(self, user_id: str) -> Optional[str]:
        """Get currently active topic for a user."""
        return self.context.get(user_id, {}).get("active_topic")
    
    def get_module_state(self, user_id: str, topic: str) -> Optional[ConvoState]:
        """Get the current state of a module for a user."""
        return self.context.get(user_id, {}).get("module_state")
    
    def clear_context(self, user_id: str) -> None:
        """Clear conversation context for a user."""
        if user_id in self.context:
            del self.context[user_id]
        self.active_topic = None 