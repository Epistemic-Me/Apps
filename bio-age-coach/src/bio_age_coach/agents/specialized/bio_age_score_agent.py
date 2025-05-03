"""Bio Age Score Agent for analyzing biological age scores."""

from typing import Dict, Any, List, Optional
from bio_age_coach.agents.base_agent import Agent
from bio_age_coach.mcp.client import MultiServerMCPClient
from bio_age_coach.router.observation_context import ObservationContext, SleepObservationContext, ExerciseObservationContext

class BioAgeScoreAgent(Agent):
    """Agent for analyzing biological age scores and providing insights."""
    
    def __init__(self, name: str, description: str, api_key: str, mcp_client):
        """Initialize the Bio Age Score agent.
        
        Args:
            name: Name of the agent
            description: Description of the agent's capabilities
            api_key: OpenAI API key
            mcp_client: MCP client for server communication
        """
        super().__init__(
            name=name,
            description=description,
            api_key=api_key,
            mcp_client=mcp_client
        )
    
    def _initialize_capabilities(self) -> None:
        """Initialize the capabilities of this agent."""
        self.capabilities = [
            "Calculate biological age score",
            "Analyze health metrics",
            "Provide age-related recommendations",
            "Interpret biomarkers",
            "Track biological age trends",
            "Suggest age optimization strategies",
            "Explain biological age factors"
        ]
    
    def _initialize_servers(self) -> None:
        """Initialize server types this agent will communicate with."""
        self.server_types = {"bio_age_score", "health"}
        
    def _initialize_domain_examples(self) -> None:
        """Initialize examples of queries this agent can handle."""
        self.domain_examples = [
            "What is my biological age?",
            "How can I reduce my biological age?",
            "What factors affect my biological age?",
            "How does my sleep affect my biological age?",
            "How does exercise impact my biological age?",
            "What's my bio age score?",
            "How has my biological age changed over time?",
            "What biomarkers are most important for biological age?",
            "How does my biological age compare to my chronological age?",
            "What lifestyle changes will most impact my biological age?",
            "How can I optimize my biological age?",
            "What's the trend in my biological age?",
            "What's causing my biological age to be higher than expected?",
            "How can I track improvements in my biological age?",
            "What's the science behind biological age calculation?"
        ]
        
    def _initialize_supported_data_types(self) -> None:
        """Initialize data types this agent can process."""
        self.supported_data_types = {"bio_age_score", "sleep", "exercise"}
    
    async def can_handle(self, query: str, context: Dict[str, Any]) -> float:
        """Determine if this agent can handle the query.
        
        Args:
            query: User query
            context: Conversation context
            
        Returns:
            float: Confidence score between 0 and 1
        """
        # Check for bio age keywords
        bio_age_keywords = [
            "biological age", "bio age", "age score", "chronological age",
            "aging", "longevity", "lifespan", "healthspan", "age optimization",
            "age reversal", "rejuvenation", "age reduction", "biomarkers",
            "biological clock", "epigenetic age", "metabolic age"
        ]
        
        # Calculate confidence based on keyword matches
        query_lower = query.lower()
        matches = sum(1 for keyword in bio_age_keywords if keyword in query_lower)
        
        # Higher confidence if multiple matches
        if matches > 2:
            return 0.95
        elif matches > 0:
            return 0.8
        
        # Check if context contains bio age data
        if context and "bio_age_score" in context:
            return 0.6
            
        return 0.3
    
    async def process(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process the query and return a response.
        
        Args:
            query: User query
            context: Conversation context
            
        Returns:
            Dict[str, Any]: Response
        """
        try:
            # Get bio age data from context or server
            bio_age_data = context.get("bio_age_score", {})
            
            if not bio_age_data:
                # Fetch bio age data from server
                response = await self.mcp_client.send_request(
                    "bio_age_score",
                    {
                        "type": "get_score",
                        "user_id": context.get("user_id", "default_user")
                    }
                )
                
                if "error" not in response:
                    bio_age_data = response
            
            # Get health data for additional context
            health_data = context.get("health_data", {})
            
            if not health_data:
                # Fetch health data from server
                response = await self.mcp_client.send_request(
                    "health",
                    {
                        "type": "metrics",
                        "timeframe": "30D"
                    }
                )
                
                if "error" not in response:
                    health_data = response.get("metrics", [])
            
            # Determine query type and route to appropriate server endpoint
            query_lower = query.lower()
            
            # Prepare request data
            request_data = {
                "user_id": context.get("user_id", "default_user"),
                "health_data": health_data,
                "bio_age_data": bio_age_data,
                "query": query
            }
            
            # Route query to appropriate server endpoint based on query type
            if any(keyword in query_lower for keyword in ["how", "reduce", "improve", "lower", "decrease", "better", "optimize", "action", "recommendation", "suggestion", "help"]):
                response = await self.mcp_client.send_request(
                    "bio_age_score",
                    {
                        "type": "process_reduction_query",
                        "data": request_data
                    }
                )
            elif "factor" in query_lower or "affect" in query_lower or "influence" in query_lower or "impact" in query_lower:
                response = await self.mcp_client.send_request(
                    "bio_age_score",
                    {
                        "type": "process_factors_query",
                        "data": request_data
                    }
                )
            elif any(keyword in query_lower for keyword in ["trend", "change", "over time", "progress", "history", "track"]):
                response = await self.mcp_client.send_request(
                    "bio_age_score",
                    {
                        "type": "process_trend_query",
                        "data": request_data
                    }
                )
            else:
                response = await self.mcp_client.send_request(
                    "bio_age_score",
                    {
                        "type": "process_score_query",
                        "data": request_data
                    }
                )
            
            # Return the response from the server
            return response
                
        except Exception as e:
            return {
                "response": "I encountered an error processing your biological age query.",
                "insights": [],
                "visualization": None,
                "error": str(e)
            }
    
    async def create_observation_context(self, data_type: str, user_id: Optional[str] = None) -> Optional[ObservationContext]:
        """Create an observation context for the given data type.
        
        Args:
            data_type: Type of data to create context for
            user_id: Optional user ID
            
        Returns:
            Optional[ObservationContext]: Observation context or None if not supported
        """
        # Check if this agent supports this data type
        if data_type == "bio_age_score":
            return ObservationContext(agent_name=self.name, data_type=data_type, user_id=user_id)
        elif data_type == "sleep":
            return SleepObservationContext(agent_name=self.name, user_id=user_id)
        elif data_type == "exercise":
            return ExerciseObservationContext(agent_name=self.name, user_id=user_id)
        
        return None 