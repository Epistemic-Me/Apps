"""
BioAge Score conversation module for the Bio Age Coach system.
Integrates with existing BioAgeScore server functionality.
"""

from typing import Dict, Any, List
from datetime import datetime
from ..core.convo_module import ConvoModule, Resource, Tool
from ..utils.client import MultiServerMCPClient

class BioAgeScoreModule(ConvoModule):
    """Module for managing bio age score conversations."""
    
    def __init__(self, api_key: str, mcp_client: MultiServerMCPClient):
        """Initialize the bio age score module."""
        super().__init__(api_key, "bio_age_score", mcp_client)
        self.user_data = {}
        self.health_data = {}  # Initialize health_data
        
        # Initialize resources and tools
        self._initialize_resources()
        self._initialize_tools()
        self._initialize_prompts()
    
    def _initialize_resources(self) -> None:
        """Initialize module resources. Resources are now managed at the server level."""
        # Register placeholder resources to ensure server types are registered
        self.add_resource("bio_age_score_data", Resource(
            name="bio_age_score_data",
            type="json",
            access_path="/bio_age_score/data",
            description="Bio age score data access point",
            server_type="bio_age_score"
        ))
        
        self.add_resource("health_data", Resource(
            name="health_data",
            type="json",
            access_path="/health/data",
            description="Health data access point",
            server_type="health"
        ))
    
    def _initialize_tools(self) -> None:
        """Initialize module tools. Tools are now managed at the server level."""
        # Register placeholder tools to ensure server types are registered
        self.add_tool("calculate_score", Tool(
            name="calculate_score",
            function=lambda x: x,  # Placeholder function
            description="Calculate bio age score",
            parameters={},
            server_type="bio_age_score"
        ))
        
        self.add_tool("fetch_health_data", Tool(
            name="fetch_health_data",
            function=lambda x: x,  # Placeholder function
            description="Fetch health data",
            parameters={},
            server_type="health"
        ))
    
    def _initialize_prompts(self) -> None:
        """Initialize conversation prompts."""
        # Load prompts from bio_age_score_prompt.py
        from ...prompts.bio_age_score_prompt import SYSTEM_PROMPT
        
        self.prompts.update({
            "collect_data": """
                I'll help you understand and improve your BioAge Score. First, let me analyze your health data:
                - Sleep duration and quality
                - Exercise and activity levels
                - Daily movement patterns
                
                I'll calculate your current score and identify opportunities for improvement.
            """,
            
            "learn_habits": """
                To provide personalized recommendations, I'd like to understand:
                1. Your typical daily schedule
                2. Sleep patterns and preferences
                3. Exercise habits and preferences
                4. Any health goals or concerns
                
                This will help me tailor suggestions to your lifestyle.
            """,
            
            "make_recommendations": """
                Based on your BioAge Score analysis:
                {recommendations}
                
                These recommendations are designed to optimize your biological age by targeting:
                - Sleep optimization (potential impact: -2 years)
                - Exercise effectiveness (potential impact: -3 years)
                - Daily movement patterns (potential impact: -1 year)
                
                Would you like more details about any of these recommendations?
            """,
            
            "answer_questions": """
                I'll help explain the science behind your BioAge Score and recommendations.
                What specific aspects would you like to know more about?
            """,
            
            "select_recommendations": """
                Excellent choices! Let's create an action plan for these improvements:
                {selected_recommendations}
                
                I'll help you track your progress and adjust the plan as needed.
                How would you like to monitor your improvements?
            """
        })
        
        # Store system prompt for reference
        self.system_prompt = SYSTEM_PROMPT
    
    async def _process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming requests."""
        try:
            request_type = request.get("type")
            if not request_type:
                return {"error": "Request type not specified"}

            if request_type == "calculate_daily_score":
                metrics = request.get("metrics", {})
                if not metrics:
                    return {"error": "No metrics provided"}
                score = await self.send_request(
                    "bio_age_score",
                    {
                        "type": "calculate_daily_score",
                        "metrics": metrics
                    }
                )
                return score

            elif request_type == "calculate_30_day_scores":
                health_data_series = request.get("metrics", {}).get("health_data_series", [])
                if not health_data_series:
                    return {"error": "No health data series provided"}
                return await self.send_request(
                    "bio_age_score",
                    {
                        "type": "calculate_30_day_scores",
                        "metrics": {
                            "health_data_series": health_data_series
                        }
                    }
                )

            elif request_type == "create_visualization":
                scores = request.get("scores", [])
                if not scores:
                    return {"error": "No scores provided"}
                return await self.send_request(
                    "bio_age_score",
                    {
                        "type": "create_visualization",
                        "scores": scores
                    }
                )

            else:
                return {"error": f"Unknown request type: {request_type}"}

        except Exception as e:
            print(f"Error processing request: {str(e)}")
            return {"error": f"Error processing request: {str(e)}"}
    
    async def initialize(self, data: Dict[str, Any]) -> None:
        """Initialize the module with user data.
        
        Args:
            data: Dictionary containing:
                - user_id: User identifier
                - health_data: User's health data series
                - habits: User's habits and preferences
                - plan: User's improvement plan
        """
        self.user_data = data
        
        # Store health data for use in _process_request
        health_data = data.get("health_data", {})
        if isinstance(health_data, dict):
            # Convert dict to list if needed
            daily_metrics = []
            for date, metrics in health_data.items():
                daily_metrics.append({
                    "date": date,
                    "sleep_hours": 7.5,  # Default test value
                    "active_calories": metrics.get("active_calories", 0),
                    "steps": metrics.get("steps", 0)
                })
            daily_metrics.sort(key=lambda x: x["date"])
            self.health_data = daily_metrics
        else:
            self.health_data = health_data
        
        # Initialize data for each server type
        for server_type in ["bio_age_score", "health"]:
            await self.send_request(
                server_type,
                {
                    "type": "initialize_data",
                    "data": {
                        "user_id": data.get("user_id"),
                        "health_data": self.health_data,
                        "habits": data.get("habits", {}),
                        "plan": data.get("plan", {})
                    }
                }
            )

    async def _fetch_health_data(self) -> List[Dict[str, Any]]:
        """Fetch health data from the health server."""
        try:
            # If we already have health data, use it
            if self.health_data:
                if isinstance(self.health_data, list):
                    return self.health_data
                else:
                    # Convert dict to list if needed
                    daily_metrics = []
                    for date, metrics in self.health_data.items():
                        daily_metrics.append({
                            "date": date,
                            "sleep_hours": 7.5,  # Default test value
                            "active_calories": metrics.get("active_calories", 0),
                            "steps": metrics.get("steps", 0)
                        })
                    daily_metrics.sort(key=lambda x: x["date"])
                    return daily_metrics
            
            # Otherwise, try to fetch from server
            response = await self.send_request(
                "health",
                {
                    "type": "metrics",
                    "timeframe": "30D",
                    "api_key": self.api_key
                }
            )
            
            if "metrics" in response:
                metrics = response["metrics"]
                if isinstance(metrics, list):
                    return metrics
                else:
                    # Convert dict to list if needed
                    daily_metrics = []
                    for date, data in metrics.items():
                        daily_metrics.append({
                            "date": date,
                            "sleep_hours": 7.5,  # Default test value
                            "active_calories": data.get("active_calories", 0),
                            "steps": data.get("steps", 0)
                        })
                    daily_metrics.sort(key=lambda x: x["date"])
                    return daily_metrics
            
            return []
            
        except Exception as e:
            print(f"Error fetching health data: {e}")
            return [] 