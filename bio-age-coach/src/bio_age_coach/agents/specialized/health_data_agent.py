"""Health Data Agent for processing health data."""

from typing import Dict, Any, List, Optional
from bio_age_coach.agents.base_agent import Agent
from bio_age_coach.mcp.client import MultiServerMCPClient
from bio_age_coach.router.observation_context import (
    ObservationContext, 
    SleepObservationContext, 
    ExerciseObservationContext,
    NutritionObservationContext,
    BiometricObservationContext
)

class HealthDataAgent(Agent):
    """Agent for processing health data and providing insights."""
    
    def __init__(self, name: str, description: str, api_key: str, mcp_client):
        """Initialize the Health Data agent.
        
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
            "Process health data",
            "Analyze health metrics",
            "Provide health insights",
            "Track fitness progress",
            "Monitor sleep patterns",
            "Analyze exercise data",
            "Provide health recommendations"
        ]
    
    def _initialize_servers(self) -> None:
        """Initialize server types this agent will communicate with."""
        self.server_types = {"health"}
        
    def _initialize_domain_examples(self) -> None:
        """Initialize examples of queries this agent can handle."""
        self.domain_examples = [
            "How is my sleep quality?",
            "What does my exercise data show?",
            "How many steps did I take yesterday?",
            "What's my average heart rate?",
            "How many calories did I burn this week?",
            "Show me my health trends",
            "How is my fitness level?",
            "What's my sleep score?",
            "How much deep sleep am I getting?",
            "What's my resting heart rate?",
            "How active have I been this month?",
            "What's my average daily step count?",
            "How many workouts did I do last week?",
            "What's my sleep efficiency?",
            "How consistent is my sleep schedule?"
        ]
        
    def _initialize_supported_data_types(self) -> None:
        """Initialize data types this agent can process."""
        self.supported_data_types = {"sleep", "exercise", "nutrition", "biometric"}
    
    async def can_handle(self, query: str, context: Dict[str, Any]) -> float:
        """Determine if this agent can handle the query.
        
        Args:
            query: User query
            context: Conversation context
            
        Returns:
            float: Confidence score between 0 and 1
        """
        # Check for health data keywords
        health_keywords = [
            "health", "sleep", "exercise", "steps", "heart rate", "calories",
            "workout", "activity", "fitness", "walking", "running", "cycling",
            "swimming", "training", "cardio", "strength", "weight lifting",
            "deep sleep", "rem sleep", "light sleep", "sleep quality",
            "resting heart rate", "active minutes", "zone minutes"
        ]
        
        # Calculate confidence based on keyword matches
        query_lower = query.lower()
        matches = sum(1 for keyword in health_keywords if keyword in query_lower)
        
        # Higher confidence if multiple matches
        if matches > 2:
            return 0.9
        elif matches > 0:
            return 0.7
        
        # Check if context contains health data
        if context and "health_data" in context:
            return 0.5
            
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
            # Get health data from context or server
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
            
            # Process query based on health data
            if "sleep" in query.lower():
                return await self._process_sleep_query(query, health_data)
            elif "exercise" in query.lower() or "workout" in query.lower():
                return await self._process_exercise_query(query, health_data)
            else:
                return await self._process_general_health_query(query, health_data)
                
        except Exception as e:
            return {
                "response": "I encountered an error processing your health data query.",
                "insights": [],
                "visualization": None,
                "error": str(e)
            }
    
    async def _process_sleep_query(self, query: str, health_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process sleep-related query.
        
        Args:
            query: User query
            health_data: Health data
            
        Returns:
            Dict[str, Any]: Response
        """
        # Extract sleep data
        sleep_data = []
        for day in health_data:
            if "sleep_hours" in day:
                sleep_data.append({
                    "date": day.get("date", ""),
                    "sleep_hours": day.get("sleep_hours", 0),
                    "deep_sleep": day.get("deep_sleep", 0),
                    "rem_sleep": day.get("rem_sleep", 0),
                    "light_sleep": day.get("light_sleep", 0)
                })
        
        if not sleep_data:
            return {
                "response": "I don't have any sleep data to analyze. Please upload your sleep data to get insights.",
                "insights": [],
                "visualization": None,
                "error": None
            }
        
        # Calculate sleep metrics
        avg_sleep = sum(day["sleep_hours"] for day in sleep_data) / len(sleep_data)
        
        # Generate insights
        insights = [
            f"Your average sleep duration is {avg_sleep:.1f} hours per night.",
            "The recommended sleep duration for adults is 7-9 hours per night."
        ]
        
        if avg_sleep < 7:
            insights.append("You're getting less sleep than recommended, which can impact your biological age.")
        elif avg_sleep > 9:
            insights.append("You're getting more sleep than average, which is generally beneficial for biological age.")
        
        # Add deep sleep insights if available
        deep_sleep_data = [day for day in sleep_data if "deep_sleep" in day and day["deep_sleep"] > 0]
        if deep_sleep_data:
            avg_deep_sleep = sum(day["deep_sleep"] for day in deep_sleep_data) / len(deep_sleep_data)
            deep_sleep_percent = (avg_deep_sleep / avg_sleep) * 100 if avg_sleep > 0 else 0
            
            insights.append(f"Your deep sleep averages {avg_deep_sleep:.1f} hours ({deep_sleep_percent:.1f}% of total sleep).")
            insights.append("Deep sleep is crucial for physical recovery and immune function.")
        
        return {
            "response": f"Based on your sleep data over the past {len(sleep_data)} days, I can provide the following analysis:",
            "insights": insights,
            "visualization": None,
            "error": None
        }
    
    async def _process_exercise_query(self, query: str, health_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process exercise-related query.
        
        Args:
            query: User query
            health_data: Health data
            
        Returns:
            Dict[str, Any]: Response
        """
        # Extract exercise data
        exercise_data = []
        for day in health_data:
            if "steps" in day or "active_calories" in day:
                exercise_data.append({
                    "date": day.get("date", ""),
                    "steps": day.get("steps", 0),
                    "active_calories": day.get("active_calories", 0),
                    "exercise_minutes": day.get("exercise_minutes", 0),
                    "heart_rate": day.get("heart_rate", 0)
                })
        
        if not exercise_data:
            return {
                "response": "I don't have any exercise data to analyze. Please upload your exercise data to get insights.",
                "insights": [],
                "visualization": None,
                "error": None
            }
        
        # Calculate exercise metrics
        avg_steps = sum(day["steps"] for day in exercise_data) / len(exercise_data)
        avg_calories = sum(day["active_calories"] for day in exercise_data) / len(exercise_data)
        
        # Generate insights
        insights = [
            f"Your average daily step count is {int(avg_steps):,} steps.",
            f"Your average active calories burned is {int(avg_calories)} calories per day.",
            "The recommended daily step count is 8,000-10,000 steps for optimal health."
        ]
        
        if avg_steps < 5000:
            insights.append("Your step count is below recommended levels, which may impact your biological age.")
        elif avg_steps > 10000:
            insights.append("Your step count is above recommended levels, which is beneficial for biological age.")
        
        return {
            "response": f"Based on your exercise data over the past {len(exercise_data)} days, I can provide the following analysis:",
            "insights": insights,
            "visualization": None,
            "error": None
        }
    
    async def _process_general_health_query(self, query: str, health_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process general health query.
        
        Args:
            query: User query
            health_data: Health data
            
        Returns:
            Dict[str, Any]: Response
        """
        if not health_data:
            return {
                "response": "I don't have any health data to analyze. Please upload your health data to get insights.",
                "insights": [],
                "visualization": None,
                "error": None
            }
        
        # Generate general health insights
        insights = []
        
        # Check for sleep data
        sleep_data = [day for day in health_data if "sleep_hours" in day]
        if sleep_data:
            avg_sleep = sum(day["sleep_hours"] for day in sleep_data) / len(sleep_data)
            insights.append(f"Your average sleep duration is {avg_sleep:.1f} hours per night.")
        
        # Check for exercise data
        exercise_data = [day for day in health_data if "steps" in day]
        if exercise_data:
            avg_steps = sum(day["steps"] for day in exercise_data) / len(exercise_data)
            insights.append(f"Your average daily step count is {int(avg_steps):,} steps.")
        
        # Check for heart rate data
        heart_rate_data = [day for day in health_data if "heart_rate" in day]
        if heart_rate_data:
            avg_heart_rate = sum(day["heart_rate"] for day in heart_rate_data) / len(heart_rate_data)
            insights.append(f"Your average resting heart rate is {int(avg_heart_rate)} bpm.")
        
        if not insights:
            insights.append("I have limited health data to analyze. Please upload more data for better insights.")
        
        return {
            "response": "Based on your health data, I can provide the following general insights:",
            "insights": insights,
            "visualization": None,
            "error": None
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
        if data_type not in self.supported_data_types:
            return None
            
        # Create appropriate observation context based on data type
        if data_type == "sleep":
            return SleepObservationContext(agent_name=self.name, user_id=user_id)
        elif data_type == "exercise":
            return ExerciseObservationContext(agent_name=self.name, user_id=user_id)
        elif data_type == "nutrition":
            return NutritionObservationContext(agent_name=self.name, user_id=user_id)
        elif data_type == "biometric":
            return BiometricObservationContext(agent_name=self.name, user_id=user_id)
        else:
            # Create a generic observation context
            return ObservationContext(agent_name=self.name, data_type=data_type, user_id=user_id) 