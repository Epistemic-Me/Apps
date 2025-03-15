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
            
            # Process query based on bio age data
            if "how" in query.lower() and "reduce" in query.lower():
                return await self._process_reduction_query(query, bio_age_data, health_data)
            elif "factor" in query.lower() or "affect" in query.lower():
                return await self._process_factors_query(query, bio_age_data, health_data)
            elif "trend" in query.lower() or "change" in query.lower() or "over time" in query.lower():
                return await self._process_trend_query(query, bio_age_data, health_data)
            else:
                return await self._process_score_query(query, bio_age_data, health_data)
                
        except Exception as e:
            return {
                "response": "I encountered an error processing your biological age query.",
                "insights": [],
                "visualization": None,
                "error": str(e)
            }
    
    async def _process_score_query(self, query: str, bio_age_data: Dict[str, Any], health_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process bio age score query.
        
        Args:
            query: User query
            bio_age_data: Bio age data
            health_data: Health data
            
        Returns:
            Dict[str, Any]: Response
        """
        # Check if we have bio age data
        if not bio_age_data or "score" not in bio_age_data:
            return {
                "response": "I don't have enough data to calculate your biological age score. Please upload more health data.",
                "insights": [
                    "Biological age calculation requires health metrics like sleep, exercise, and biomarkers.",
                    "Regular tracking of health data improves the accuracy of biological age estimation."
                ],
                "visualization": None,
                "error": None
            }
        
        # Extract bio age score
        bio_age_score = bio_age_data.get("score", 0)
        chronological_age = bio_age_data.get("chronological_age", 0)
        
        # Generate insights
        insights = []
        
        if chronological_age > 0:
            age_difference = bio_age_score - chronological_age
            
            if age_difference < -5:
                insights.append(f"Your biological age is {abs(age_difference):.1f} years younger than your chronological age, indicating excellent health practices.")
            elif age_difference < 0:
                insights.append(f"Your biological age is {abs(age_difference):.1f} years younger than your chronological age, suggesting good health practices.")
            elif age_difference < 5:
                insights.append(f"Your biological age is {age_difference:.1f} years older than your chronological age, indicating room for improvement.")
            else:
                insights.append(f"Your biological age is {age_difference:.1f} years older than your chronological age, suggesting significant health optimization opportunities.")
        
        # Add insights based on health data
        if health_data:
            sleep_data = [day for day in health_data if "sleep_hours" in day]
            if sleep_data:
                avg_sleep = sum(day["sleep_hours"] for day in sleep_data) / len(sleep_data)
                if avg_sleep < 7:
                    insights.append(f"Your average sleep of {avg_sleep:.1f} hours may be contributing to a higher biological age.")
                else:
                    insights.append(f"Your average sleep of {avg_sleep:.1f} hours supports a lower biological age.")
            
            exercise_data = [day for day in health_data if "steps" in day]
            if exercise_data:
                avg_steps = sum(day["steps"] for day in exercise_data) / len(exercise_data)
                if avg_steps < 5000:
                    insights.append(f"Your average of {int(avg_steps):,} steps per day may be contributing to a higher biological age.")
                else:
                    insights.append(f"Your average of {int(avg_steps):,} steps per day supports a lower biological age.")
        
        # Create visualization data
        visualization = None
        if "history" in bio_age_data:
            history = bio_age_data["history"]
            dates = [entry.get("date", "") for entry in history]
            scores = [entry.get("score", 0) for entry in history]
            
            if dates and scores:
                visualization = {
                    "dates": dates,
                    "scores": scores,
                    "reference_ranges": {
                        "optimal_min": [chronological_age - 5] * len(dates) if chronological_age > 0 else [bio_age_score - 5] * len(dates),
                        "optimal_max": [chronological_age] * len(dates) if chronological_age > 0 else [bio_age_score] * len(dates),
                        "good_min": [chronological_age - 10] * len(dates) if chronological_age > 0 else [bio_age_score - 10] * len(dates),
                        "good_max": [chronological_age + 5] * len(dates) if chronological_age > 0 else [bio_age_score + 5] * len(dates)
                    }
                }
        
        return {
            "response": f"Your current biological age score is {bio_age_score:.1f} years." if chronological_age == 0 else f"Your biological age is {bio_age_score:.1f} years compared to your chronological age of {chronological_age} years.",
            "insights": insights,
            "visualization": visualization,
            "error": None
        }
    
    async def _process_reduction_query(self, query: str, bio_age_data: Dict[str, Any], health_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process bio age reduction query.
        
        Args:
            query: User query
            bio_age_data: Bio age data
            health_data: Health data
            
        Returns:
            Dict[str, Any]: Response
        """
        # Generate recommendations
        recommendations = [
            "Optimize sleep: Aim for 7-9 hours of quality sleep per night.",
            "Regular exercise: Include both cardio and strength training.",
            "Nutrition: Focus on a plant-rich diet with adequate protein.",
            "Stress management: Practice meditation or other stress-reduction techniques.",
            "Social connections: Maintain strong social relationships.",
            "Cognitive stimulation: Engage in learning and mentally challenging activities.",
            "Avoid toxins: Limit alcohol, avoid smoking, and minimize exposure to environmental toxins."
        ]
        
        # Personalize recommendations based on health data
        if health_data:
            sleep_data = [day for day in health_data if "sleep_hours" in day]
            if sleep_data:
                avg_sleep = sum(day["sleep_hours"] for day in sleep_data) / len(sleep_data)
                if avg_sleep < 7:
                    recommendations.insert(0, f"Increase sleep duration: Your current average of {avg_sleep:.1f} hours is below optimal. Aim for at least 7 hours.")
            
            exercise_data = [day for day in health_data if "steps" in day]
            if exercise_data:
                avg_steps = sum(day["steps"] for day in exercise_data) / len(exercise_data)
                if avg_steps < 8000:
                    recommendations.insert(1, f"Increase physical activity: Your current average of {int(avg_steps):,} steps is below optimal. Aim for at least 8,000-10,000 steps daily.")
        
        return {
            "response": "Here are evidence-based strategies to reduce your biological age:",
            "insights": recommendations,
            "visualization": None,
            "error": None
        }
    
    async def _process_factors_query(self, query: str, bio_age_data: Dict[str, Any], health_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process bio age factors query.
        
        Args:
            query: User query
            bio_age_data: Bio age data
            health_data: Health data
            
        Returns:
            Dict[str, Any]: Response
        """
        # Generate factors
        factors = [
            "Sleep quality and duration: Affects cellular repair, hormone regulation, and immune function.",
            "Physical activity: Influences cardiovascular health, muscle mass, and metabolic function.",
            "Nutrition: Impacts inflammation, cellular health, and metabolic processes.",
            "Stress levels: Affects telomere length, inflammation, and cellular aging.",
            "Social connections: Strong relationships are associated with longevity and reduced biological age.",
            "Cognitive engagement: Mental stimulation supports brain health and cognitive resilience.",
            "Environmental exposures: Toxins, pollution, and UV radiation can accelerate aging."
        ]
        
        # Personalize factors based on health data
        personalized_insights = []
        
        if health_data:
            sleep_data = [day for day in health_data if "sleep_hours" in day]
            if sleep_data:
                avg_sleep = sum(day["sleep_hours"] for day in sleep_data) / len(sleep_data)
                if avg_sleep < 7:
                    personalized_insights.append(f"Your average sleep of {avg_sleep:.1f} hours may be increasing your biological age. Each additional hour of sleep (up to 8 hours) can reduce biological age by approximately 0.3-0.5 years.")
                else:
                    personalized_insights.append(f"Your average sleep of {avg_sleep:.1f} hours supports a lower biological age.")
            
            exercise_data = [day for day in health_data if "steps" in day]
            if exercise_data:
                avg_steps = sum(day["steps"] for day in exercise_data) / len(exercise_data)
                if avg_steps < 5000:
                    personalized_insights.append(f"Your average of {int(avg_steps):,} steps per day may be increasing your biological age. Increasing to 7,500+ steps daily can reduce biological age by approximately 0.5-1.0 years.")
                else:
                    personalized_insights.append(f"Your average of {int(avg_steps):,} steps per day supports a lower biological age.")
        
        # Combine general factors with personalized insights
        all_insights = factors + personalized_insights if personalized_insights else factors
        
        return {
            "response": "The following factors influence your biological age:",
            "insights": all_insights,
            "visualization": None,
            "error": None
        }
    
    async def _process_trend_query(self, query: str, bio_age_data: Dict[str, Any], health_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process bio age trend query.
        
        Args:
            query: User query
            bio_age_data: Bio age data
            health_data: Health data
            
        Returns:
            Dict[str, Any]: Response
        """
        # Check if we have history data
        if not bio_age_data or "history" not in bio_age_data or not bio_age_data["history"]:
            return {
                "response": "I don't have enough historical data to show trends in your biological age. Continue tracking your health metrics to build this data over time.",
                "insights": [
                    "Biological age trends require regular tracking of health metrics.",
                    "Weekly or monthly assessments provide the best insights into biological age changes."
                ],
                "visualization": None,
                "error": None
            }
        
        # Extract history data
        history = bio_age_data["history"]
        dates = [entry.get("date", "") for entry in history]
        scores = [entry.get("score", 0) for entry in history]
        
        # Calculate trend
        if len(scores) >= 2:
            first_score = scores[0]
            last_score = scores[-1]
            change = last_score - first_score
            
            # Generate insights
            insights = []
            
            if change < -1:
                insights.append(f"Your biological age has decreased by {abs(change):.1f} years over the tracked period, showing excellent progress.")
            elif change < 0:
                insights.append(f"Your biological age has decreased slightly by {abs(change):.1f} years, showing positive progress.")
            elif change < 1:
                insights.append(f"Your biological age has remained relatively stable, changing by only {change:.1f} years.")
            else:
                insights.append(f"Your biological age has increased by {change:.1f} years, suggesting opportunities for health optimization.")
            
            # Add insights about contributing factors
            if health_data:
                # Split health data into earlier and later periods
                mid_point = len(health_data) // 2
                earlier_data = health_data[:mid_point]
                later_data = health_data[mid_point:]
                
                # Compare sleep patterns
                earlier_sleep = [day for day in earlier_data if "sleep_hours" in day]
                later_sleep = [day for day in later_data if "sleep_hours" in day]
                
                if earlier_sleep and later_sleep:
                    avg_earlier_sleep = sum(day["sleep_hours"] for day in earlier_sleep) / len(earlier_sleep)
                    avg_later_sleep = sum(day["sleep_hours"] for day in later_sleep) / len(later_sleep)
                    sleep_change = avg_later_sleep - avg_earlier_sleep
                    
                    if abs(sleep_change) > 0.5:
                        if sleep_change > 0:
                            insights.append(f"Your average sleep has increased by {sleep_change:.1f} hours, which may be contributing to the observed biological age changes.")
                        else:
                            insights.append(f"Your average sleep has decreased by {abs(sleep_change):.1f} hours, which may be contributing to the observed biological age changes.")
                
                # Compare activity patterns
                earlier_steps = [day for day in earlier_data if "steps" in day]
                later_steps = [day for day in later_data if "steps" in day]
                
                if earlier_steps and later_steps:
                    avg_earlier_steps = sum(day["steps"] for day in earlier_steps) / len(earlier_steps)
                    avg_later_steps = sum(day["steps"] for day in later_steps) / len(later_steps)
                    steps_change = avg_later_steps - avg_earlier_steps
                    
                    if abs(steps_change) > 1000:
                        if steps_change > 0:
                            insights.append(f"Your average daily steps have increased by {int(steps_change):,}, which may be contributing to the observed biological age changes.")
                        else:
                            insights.append(f"Your average daily steps have decreased by {int(abs(steps_change)):,}, which may be contributing to the observed biological age changes.")
            
            # Create visualization
            chronological_age = bio_age_data.get("chronological_age", 0)
            visualization = {
                "dates": dates,
                "scores": scores,
                "reference_ranges": {
                    "optimal_min": [chronological_age - 5] * len(dates) if chronological_age > 0 else [min(scores) - 5] * len(dates),
                    "optimal_max": [chronological_age] * len(dates) if chronological_age > 0 else [min(scores)] * len(dates),
                    "good_min": [chronological_age - 10] * len(dates) if chronological_age > 0 else [min(scores) - 10] * len(dates),
                    "good_max": [chronological_age + 5] * len(dates) if chronological_age > 0 else [min(scores) + 5] * len(dates)
                }
            }
            
            return {
                "response": f"Your biological age has changed from {first_score:.1f} to {last_score:.1f} years over the tracked period.",
                "insights": insights,
                "visualization": visualization,
                "error": None
            }
        else:
            return {
                "response": "I only have one data point for your biological age, so I can't show a trend yet. Continue tracking your health metrics to build this data over time.",
                "insights": [
                    "Your current biological age score is " + str(scores[0]) + " years.",
                    "Regular tracking will help establish trends in your biological age."
                ],
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
        if data_type == "bio_age_score":
            return ObservationContext(agent_name=self.name, data_type=data_type, user_id=user_id)
        elif data_type == "sleep":
            return SleepObservationContext(agent_name=self.name, user_id=user_id)
        elif data_type == "exercise":
            return ExerciseObservationContext(agent_name=self.name, user_id=user_id)
        
        return None 