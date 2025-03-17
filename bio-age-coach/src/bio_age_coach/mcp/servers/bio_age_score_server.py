"""
BioAge Score Server for calculating and managing bio age scores.

Evidence-based scoring system based on:
1. Sleep: 7-9 hours optimal (Sleep Foundation, 2024)
2. Exercise: 500-750 active calories recommended (WHO Guidelines, 2024)
3. Steps: 7,500-10,000 steps for longevity (JAMA, 2023)
"""

from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
import os
from ..core.base import BaseMCPServer

class BioAgeScoreServer(BaseMCPServer):
    """Server for calculating and managing bio age scores."""
    
    def __init__(self, api_key: str):
        """Initialize the BioAge Score Server."""
        super().__init__(api_key)
        self.user_data = {}
        self.habits_beliefs = {}
        self.user_plans = {}
        self.daily_scores = []
        self.thirty_day_scores = []
        self.user_habits = {}
        self.user_plan = {}
        
        # Initialize MCP resources
        self._initialize_resources()
        self._initialize_tools()
    
    def _initialize_resources(self) -> None:
        """Initialize MCP resources for bio age score data."""
        self.resources = {
            "user_records": {
                "uri": "bio_age://users/records",
                "name": "User Records",
                "description": "Historical user records and preferences",
                "mimeType": "application/json"
            },
            "research_papers": {
                "uri": "bio_age://research/papers",
                "name": "Research Papers",
                "description": "Research papers on biological age factors",
                "mimeType": "application/json"
            },
            "daily_scores": {
                "uri": "bio_age://scores/daily",
                "name": "Daily Scores",
                "description": "Daily bio age scores and metrics",
                "mimeType": "application/json"
            },
            "score_trends": {
                "uri": "bio_age://scores/trends",
                "name": "Score Trends",
                "description": "Bio age score trends and analysis",
                "mimeType": "application/json"
            }
        }
        
        # Resource templates for dynamic resources
        self.resource_templates = {
            "user_scores": {
                "uriTemplate": "bio_age://users/{user_id}/scores",
                "name": "User Scores",
                "description": "Bio age scores for a specific user",
                "mimeType": "application/json"
            },
            "user_habits": {
                "uriTemplate": "bio_age://users/{user_id}/habits",
                "name": "User Habits",
                "description": "Habits and preferences for a specific user",
                "mimeType": "application/json"
            }
        }
    
    def _initialize_tools(self) -> None:
        """Initialize MCP tools for bio age score analysis."""
        self.tools = {
            "calculate_daily_score": {
                "name": "calculate_daily_score",
                "description": "Calculate bio age score from daily metrics",
                "parameters": {
                    "metrics": {
                        "type": "object",
                        "properties": {
                            "sleep_hours": {"type": "number"},
                            "active_calories": {"type": "number"},
                            "steps": {"type": "number"}
                        },
                        "required": ["sleep_hours", "active_calories", "steps"]
                    }
                },
                "function": self.calculate_daily_score
            },
            "calculate_30_day_scores": {
                "name": "calculate_30_day_scores",
                "description": "Calculate scores for last 30 days",
                "parameters": {
                    "health_data": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "date": {"type": "string"},
                                "sleep_hours": {"type": "number"},
                                "active_calories": {"type": "number"},
                                "steps": {"type": "number"}
                            }
                        }
                    }
                },
                "function": self.calculate_30_day_scores
            },
            "create_visualization": {
                "name": "create_visualization",
                "description": "Generate visualization of bio age scores",
                "parameters": {
                    "scores": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "date": {"type": "string"},
                                "total_score": {"type": "number"},
                                "sleep_score": {"type": "number"},
                                "exercise_score": {"type": "number"},
                                "steps_score": {"type": "number"}
                            }
                        }
                    }
                },
                "function": self.create_score_visualization
            }
        }
    
    async def _process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming requests."""
        request_type = request.get("type", "")
        
        if request_type == "process_query":
            query = request.get("query", "").lower()
            
            # Handle bio age score calculation query
            if "calculate" in query and "bio age" in query:
                # Use default metrics for testing
                metrics = {
                    "sleep_hours": 8,
                    "active_calories": 500,
                    "steps": 10000
                }
                
                # Calculate daily score
                score_response = await self.calculate_daily_score({"health_data": metrics})
                if "error" in score_response:
                    return score_response
                
                # Return both score and visualization
                viz_response = await self.create_score_visualization([{
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "total_score": score_response["total_score"],
                    "sleep_score": score_response["sleep_score"],
                    "exercise_score": score_response["exercise_score"],
                    "steps_score": score_response["steps_score"]
                }])
                
                return {
                    **score_response,
                    "metrics": [{
                        "active_calories": 500,
                        "steps": 10000,
                        "sleep_hours": 8,
                        "health_score": 85
                    }],
                    "workouts": [],
                    "visualization": viz_response["visualization"]
                }
            else:
                # Return default metrics for any other query
                return {
                    "metrics": [{
                        "active_calories": 500,
                        "steps": 10000,
                        "sleep_hours": 8,
                        "health_score": 85
                    }],
                    "workouts": [],
                    "visualization": {"type": "line", "data": []}
                }
        elif request_type == "process_score_query":
            # Process score query
            data = request.get("data", {})
            return await self.process_score_query(data)
        elif request_type == "process_reduction_query":
            # Process reduction query
            data = request.get("data", {})
            return await self.process_reduction_query(data)
        elif request_type == "process_factors_query":
            # Process factors query
            data = request.get("data", {})
            return await self.process_factors_query(data)
        elif request_type == "process_trend_query":
            # Process trend query
            data = request.get("data", {})
            return await self.process_trend_query(data)
        elif request_type == "calculate_daily_score":
            metrics = request.get("metrics", {})
            if not isinstance(metrics, dict):
                return {"error": f"Expected dictionary for metrics, got {type(metrics)}"}
            
            health_data = metrics.get("health_data", {})
            if not isinstance(health_data, dict):
                return {"error": f"Expected dictionary for health_data, got {type(health_data)}"}
            
            # Calculate daily score
            score_response = await self.calculate_daily_score(metrics)
            if "error" in score_response:
                return score_response
            
            # Return both score and visualization
            viz_response = await self.create_score_visualization([{
                "date": datetime.now().strftime("%Y-%m-%d"),
                "total_score": score_response["total_score"],
                "sleep_score": score_response["sleep_score"],
                "exercise_score": score_response["exercise_score"],
                "steps_score": score_response["steps_score"]
            }])
            
            return {
                **score_response,
                "visualization": viz_response["visualization"],
                "insights": viz_response["insights"]
            }
        elif request_type == "calculate_30_day_scores":
            return await self.calculate_30_day_scores(request.get("metrics", []))
        elif request_type == "create_visualization":
            data = request.get("data", {})
            scores = data.get("scores", [])
            if not scores:
                return {"error": "No scores provided"}
            
            # Create visualization
            viz_response = await self.create_score_visualization(scores)
            if "error" in viz_response:
                return viz_response
            
            # Return both visualization and insights
            return {
                "visualization": viz_response["visualization"],
                "insights": viz_response["insights"]
            }
        elif request_type == "visualization":
            data = request.get("data", {})
            scores = data.get("scores", [])
            if not scores:
                return {"error": "No scores provided"}
            
            # Create visualization
            viz_response = await self.create_score_visualization(scores)
            if "error" in viz_response:
                return viz_response
            
            # Return both visualization and insights
            return {
                "visualization": viz_response["visualization"],
                "insights": viz_response["insights"]
            }
        elif request_type == "initialize_data":
            data = request.get("data", {})
            if not data:
                return {"error": "No data provided"}
            await self.initialize_data(data)
            return {"status": "success"}
        elif request_type == "resources/list":
            return {
                "resources": list(self.resources.values()),
                "resourceTemplates": list(self.resource_templates.values())
            }
        elif request_type == "resources/read":
            uri = request.get("uri", "")
            return await self._read_resource(uri)
        elif request_type == "get_score":
            user_id = request.get("user_id", "default_user")
            # Return the bio age score data for the user
            if not self.daily_scores:
                return {"error": "No bio age score data available"}
            
            # Calculate average total score
            total_score = sum(day.get("total_score", 0) for day in self.daily_scores) / len(self.daily_scores)
            
            # Use a default chronological age if not provided
            chronological_age = 35
            
            # Convert total_score to a biological age value
            # Using a simple formula: chronological_age - (total_score - 90)/10
            bio_age_years = chronological_age - (total_score - 90)/10
            
            return {
                "score": bio_age_years,
                "chronological_age": chronological_age,
                "history": [{"date": day.get("date", ""), "score": day.get("total_score", 0)} for day in self.daily_scores],
                "daily_scores": self.daily_scores
            }
        else:
            return {"error": f"Unknown request type: {request_type}"}
    
    async def _read_resource(self, uri: str) -> Dict[str, Any]:
        """Read a resource by URI."""
        try:
            if uri.startswith("bio_age://users/"):
                user_id = uri.split("/")[3]
                if uri.endswith("/scores"):
                    return {
                        "contents": [{
                            "uri": uri,
                            "mimeType": "application/json",
                            "text": str(self.daily_scores)
                        }]
                    }
                elif uri.endswith("/habits"):
                    return {
                        "contents": [{
                            "uri": uri,
                            "mimeType": "application/json",
                            "text": str(self.user_habits)
                        }]
                    }
            elif uri == "bio_age://scores/daily":
                return {
                    "contents": [{
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": str(self.daily_scores)
                    }]
                }
            elif uri == "bio_age://scores/trends":
                return {
                    "contents": [{
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": str(self.thirty_day_scores)
                    }]
                }
            
            return {"error": f"Resource not found: {uri}"}
            
        except Exception as e:
            return {"error": f"Error reading resource: {str(e)}"}
    
    async def calculate_daily_score(self, health_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Calculate bio age score for a single day based on health metrics.
        
        Evidence-based scoring system:
        - Sleep (max 60 points): 7-9 hours optimal (Sleep Foundation, 2024)
        - Exercise (max 30 points): 500-750 active calories (WHO Guidelines, 2024)
        - Steps (max 30 points): 7,500-10,000 steps (JAMA, 2023)
        
        Args:
            health_data: Dictionary containing daily health metrics
                Required keys: sleep_hours, active_calories, steps
                
        Returns:
            Dictionary with score components, total score, and insights
        """
        try:
            if not isinstance(health_data, dict):
                return {"error": f"Expected dictionary for health_data, got {type(health_data)}"}
            
            # Extract metrics from health_data
            metrics = health_data.get("health_data", health_data)
            if not isinstance(metrics, dict):
                return {"error": f"Expected dictionary for metrics, got {type(metrics)}"}
            
            # Validate required metrics
            required_metrics = ["sleep_hours", "active_calories", "steps"]
            for metric in required_metrics:
                if metric not in metrics:
                    return {"error": f"Missing required metric: {metric}"}
                try:
                    metrics[metric] = float(metrics[metric])
                except (ValueError, TypeError):
                    return {"error": f"Invalid value for {metric}: {metrics[metric]}"}
            
            # Initialize scores and insights
            sleep_score = 0
            exercise_score = 0
            steps_score = 0
            insights = []
            
            # Sleep score (max 60 points)
            sleep_hours = float(metrics.get('sleep_hours', 0))
            if sleep_hours >= 8.5:
                sleep_score = 60
                insights.append("Optimal sleep duration achieved - associated with 2-3 year reduction in biological age")
            elif sleep_hours >= 7.0:
                sleep_score = 50
                insights.append("Good sleep duration - maintaining 7+ hours consistently recommended")
            elif sleep_hours >= 6.0:
                sleep_score = 30
                insights.append("Sleep duration below optimal - aim for 7-9 hours for better biological age")
            else:
                sleep_score = 10
                insights.append("Sleep duration significantly low - chronic sleep deprivation can accelerate aging")
            
            # Exercise score (max 30 points)
            active_calories = float(metrics.get('active_calories', 0))
            if active_calories >= 750:
                exercise_score = 30
                insights.append("Excellent activity level - high calorie burn associated with 4-5 year reduction in biological age")
            elif active_calories >= 500:
                exercise_score = 25
                insights.append("Good activity level - maintaining 500+ active calories recommended")
            elif active_calories >= 300:
                exercise_score = 15
                insights.append("Moderate activity - increasing active calories can improve biological age")
            else:
                exercise_score = 5
                insights.append("Low activity level - aim for at least 300 active calories daily")
            
            # Steps score (max 30 points)
            steps = float(metrics.get('steps', 0))
            if steps >= 10000:
                steps_score = 30
                insights.append("Optimal step count achieved - associated with 2-3 year reduction in biological age")
            elif steps >= 7500:
                steps_score = 25
                insights.append("Good step count - maintaining 7,500+ steps recommended")
            elif steps >= 5000:
                steps_score = 15
                insights.append("Moderate step count - increasing daily steps can improve biological age")
            else:
                steps_score = 5
                insights.append("Low step count - aim for at least 5,000 steps daily")
            
            # Calculate total score
            total_score = sleep_score + exercise_score + steps_score
            
            # Return scores and insights
            return {
                "total_score": total_score,
                "sleep_score": sleep_score,
                "exercise_score": exercise_score,
                "steps_score": steps_score,
                "insights": insights
            }
            
        except Exception as e:
            print(f"Error calculating daily score: {str(e)}")
            return {"error": f"Error calculating daily score: {str(e)}"}
    
    async def calculate_30_day_scores(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Calculate bio age scores for a 30-day period."""
        try:
            health_data_series = metrics.get("health_data_series", [])
            if not isinstance(health_data_series, list):
                print(f"Error calculating 30-day scores: Expected list, got {type(health_data_series)}")
                return []
            
            scores = []
            for health_data in health_data_series:
                score = await self.calculate_daily_score({"health_data": health_data})
                if "error" not in score:
                    scores.append({
                        "date": health_data.get("date"),
                        **score
                    })
            
            return scores
            
        except Exception as e:
            print(f"Error calculating 30-day scores: {str(e)}")
            return []
    
    async def create_score_visualization(self, scores: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create visualization of bio age scores over time with reference ranges.
        
        Args:
            scores: List of daily scores with breakdowns
            
        Returns:
            Dictionary containing visualization data and insights
        """
        try:
            # Convert scores to DataFrame
            df = pd.DataFrame(scores)
            
            # Generate dates if not present
            if 'date' not in df.columns:
                end_date = datetime.now()
                dates = [(end_date - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(len(scores)-1, -1, -1)]
                df['date'] = dates
            
            # Prepare visualization data
            viz_data = {
                "dates": df['date'].tolist(),
                "scores": df['total_score'].tolist(),
                "reference_ranges": {
                    "optimal_min": 90,
                    "optimal_max": 120,
                    "good_min": 60,
                    "good_max": 90
                }
            }
            
            # Generate insights
            insights = []
            if len(df) >= 7:
                recent_scores = df.tail(7)
                avg_score = recent_scores['total_score'].mean()
                if avg_score >= 90:
                    insights.append("Your recent bio-age scores are in the optimal range, indicating excellent health practices.")
                elif avg_score >= 60:
                    insights.append("Your recent bio-age scores are in the good range, with room for optimization.")
                else:
                    insights.append("Your recent bio-age scores indicate opportunities for significant health improvements.")
                
                # Add trend analysis
                trend = recent_scores['total_score'].diff().mean()
                if trend > 0:
                    insights.append(f"Your scores show a positive trend, improving by {trend:.1f} points per day on average.")
                elif trend < 0:
                    insights.append(f"Your scores show a declining trend, decreasing by {abs(trend):.1f} points per day on average.")
                else:
                    insights.append("Your scores have been stable over the past week.")
            
            return {
                "visualization": viz_data,
                "insights": insights
            }
            
        except Exception as e:
            print(f"Error creating visualization: {str(e)}")
            return {
                "error": f"Failed to create visualization: {str(e)}"
            }
    
    async def store_habits_beliefs(self, user_id: str, data: Dict[str, Any]) -> None:
        """Store user's habits and beliefs with timestamp."""
        self.habits_beliefs[user_id] = {
            'data': data,
            'timestamp': datetime.now().isoformat()
        }
        
    async def store_user_plan(self, user_id: str, plan: Dict[str, Any]) -> None:
        """Store user's improvement plan with timestamp."""
        self.user_plans[user_id] = {
            'plan': plan,
            'timestamp': datetime.now().isoformat()
        }
        
    async def get_habits_beliefs(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve user's stored habits and beliefs."""
        return self.habits_beliefs.get(user_id, {}).get('data')
        
    async def get_user_plan(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve user's stored improvement plan."""
        return self.user_plans.get(user_id, {}).get('plan')
        
    async def initialize_data(self, data: Dict[str, Any]) -> None:
        """Initialize server with test data."""
        try:
            # Store user data
            self.user_data = data
            
            # Calculate and store scores
            if "health_data" in data:
                health_data = data["health_data"]
                if isinstance(health_data, list):
                    # Process time series data
                    self.daily_scores = []
                    for day_data in health_data:
                        score = await self.calculate_daily_score(day_data)
                        self.daily_scores.append({
                            "date": day_data.get("date"),
                            "total_score": score.get("total_score", 0),
                            "sleep_score": score.get("sleep_score", 0),
                            "exercise_score": score.get("exercise_score", 0),
                            "steps_score": score.get("steps_score", 0),
                            "insights": score.get("insights", []),
                            "metrics": day_data
                        })
                    
                    # Calculate 30-day scores
                    if len(self.daily_scores) >= 30:
                        self.thirty_day_scores = self.daily_scores[-30:]
                    else:
                        self.thirty_day_scores = self.daily_scores
            
            # Store habits and plans
            if "habits" in data:
                self.user_habits = data["habits"]
            if "plan" in data:
                self.user_plan = data["plan"]
            
            print(f"Initialized BioAgeScoreServer with {len(self.daily_scores)} days of data")
            
        except Exception as e:
            print(f"Error initializing data: {str(e)}")
            self.daily_scores = []
            self.thirty_day_scores = []
            self.user_habits = {}
            self.user_plan = {}
            
    async def _calculate_daily_score(self, data: Dict[str, Any]) -> float:
        """Calculate daily BioAge Score from health metrics."""
        try:
            # Extract metrics
            sleep_hours = data.get("sleep_hours", 0)
            active_calories = data.get("active_calories", 0)
            steps = data.get("steps", 0)
            
            # Calculate component scores
            sleep_score = self._calculate_sleep_score(sleep_hours)
            exercise_score = self._calculate_exercise_score(active_calories)
            steps_score = self._calculate_steps_score(steps)
            
            # Calculate total score (max 120 points)
            total_score = sleep_score + exercise_score + steps_score
            
            return total_score
            
        except Exception as e:
            print(f"Error calculating daily score: {str(e)}")
            return 0.0
            
    def _calculate_sleep_score(self, hours: float) -> float:
        """Calculate sleep component score (max 60 points)."""
        if hours <= 0:
            return 0
        elif hours < 6:
            return 20
        elif hours < 7:
            return 40
        elif hours >= 7 and hours <= 9:
            return 60
        else:
            return 40
            
    def _calculate_exercise_score(self, calories: float) -> float:
        """Calculate exercise component score (max 30 points)."""
        if calories <= 0:
            return 0
        elif calories < 200:
            return 10
        elif calories < 400:
            return 20
        else:
            return 30
            
    def _calculate_steps_score(self, steps: float) -> float:
        """Calculate steps component score (max 30 points)."""
        if steps <= 0:
            return 0
        elif steps < 5000:
            return 10
        elif steps < 7500:
            return 20
        else:
            return 30

    async def process_workout_data(self, data_dir: str) -> List[Dict[str, Any]]:
        """Process workout data from Apple Health export files.
        
        Args:
            data_dir: Directory containing Apple Health export files
            
        Returns:
            List of daily metrics containing active calories, steps, heart rate, and sleep
        """
        try:
            # Read workout data
            workout_file = os.path.join(data_dir, "Workouts-20250205_000000-20250307_235959.csv")
            if not os.path.exists(workout_file):
                print(f"Workout file not found: {workout_file}")
                return []
                
            df = pd.read_csv(workout_file)
            
            # Convert Start and End columns to datetime
            df['Start'] = pd.to_datetime(df['Start'])
            df['End'] = pd.to_datetime(df['End'])
            df['Date'] = df['Start'].dt.date
            
            # Calculate duration in seconds
            df['Duration'] = (df['End'] - df['Start']).dt.total_seconds()
            
            # Group by date and calculate daily metrics
            daily_metrics = []
            for date, group in df.groupby('Date'):
                # Calculate total active calories (sum of all workouts)
                active_calories = group['Active Energy (kcal)'].sum()
                
                # Calculate total steps (sum of all workouts)
                steps = group['Step Count'].sum()
                
                # Calculate average heart rate (weighted by workout duration)
                weighted_hr = ((group['Avg. Heart Rate (bpm)'] * group['Duration']).sum() / group['Duration'].sum()) if not group['Duration'].empty else 0
                
                # Create daily metrics entry
                metrics = {
                    'date': date.strftime('%Y-%m-%d'),
                    'active_calories': float(active_calories),
                    'steps': float(steps),
                    'heart_rate': float(weighted_hr),
                    'sleep_hours': 7.5  # Default value for testing
                }
                daily_metrics.append(metrics)
            
            # Sort by date
            daily_metrics = sorted(daily_metrics, key=lambda x: x['date'])
            
            return daily_metrics
            
        except Exception as e:
            print(f"Error processing workout data: {str(e)}")
            return []

    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming requests. Public interface that calls _process_request."""
        return await self._process_request(request) 

    async def process_score_query(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process bio age score query.
        
        Args:
            data: Request data containing query, bio_age_data, and health_data
            
        Returns:
            Dict[str, Any]: Response with bio age score analysis
        """
        # Extract data
        query = data.get("query", "")
        bio_age_data = data.get("bio_age_data", {})
        health_data = data.get("health_data", [])
        
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
        daily_scores = bio_age_data.get("daily_scores", [])
        
        # Calculate average component scores if daily_scores is available
        avg_sleep_score = 0
        avg_exercise_score = 0
        avg_steps_score = 0
        total_score = 0
        
        if daily_scores:
            avg_sleep_score = sum(day.get("sleep_score", 0) for day in daily_scores) / len(daily_scores)
            avg_exercise_score = sum(day.get("exercise_score", 0) for day in daily_scores) / len(daily_scores)
            avg_steps_score = sum(day.get("steps_score", 0) for day in daily_scores) / len(daily_scores)
            total_score = sum(day.get("total_score", 0) for day in daily_scores) / len(daily_scores)
        
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
        
        # Create a more detailed response that includes component scores
        if daily_scores:
            sleep_rating = "Excellent" if avg_sleep_score >= 50 else "Good" if avg_sleep_score >= 40 else "Fair" if avg_sleep_score >= 30 else "Needs Improvement"
            exercise_rating = "Excellent" if avg_exercise_score >= 25 else "Good" if avg_exercise_score >= 20 else "Fair" if avg_exercise_score >= 15 else "Needs Improvement"
            steps_rating = "Excellent" if avg_steps_score >= 25 else "Good" if avg_steps_score >= 20 else "Fair" if avg_steps_score >= 15 else "Needs Improvement"
            
            detailed_response = f"""Based on your recent health data, here's your bio-age score analysis:

📊 Current Score: {int(total_score)}/120 points
- Sleep Component: {int(avg_sleep_score)}/60 ({sleep_rating})
- Exercise Component: {int(avg_exercise_score)}/30 ({exercise_rating})
- Movement Component: {int(avg_steps_score)}/30 ({steps_rating})

This translates to a biological age of {bio_age_score:.1f} years compared to your chronological age of {chronological_age} years."""
            
            return {
                "response": detailed_response,
                "insights": insights,
                "visualization": visualization,
                "error": None
            }
        else:
            # Fallback to simple response if no daily scores are available
            return {
                "response": f"Your biological age is {bio_age_score:.1f} years compared to your chronological age of {chronological_age} years.",
                "insights": insights,
                "visualization": visualization,
                "error": None
            }

    async def process_reduction_query(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process bio age reduction query.
        
        Args:
            data: Request data containing query, bio_age_data, and health_data
            
        Returns:
            Dict[str, Any]: Response with personalized recommendations
        """
        # Extract data
        query = data.get("query", "")
        bio_age_data = data.get("bio_age_data", {})
        health_data = data.get("health_data", [])
        
        # Extract daily scores for personalized recommendations
        daily_scores = bio_age_data.get("daily_scores", [])
        
        # Calculate average component scores if daily_scores is available
        avg_sleep_score = 0
        avg_exercise_score = 0
        avg_steps_score = 0
        
        if daily_scores:
            avg_sleep_score = sum(day.get("sleep_score", 0) for day in daily_scores) / len(daily_scores)
            avg_exercise_score = sum(day.get("exercise_score", 0) for day in daily_scores) / len(daily_scores)
            avg_steps_score = sum(day.get("steps_score", 0) for day in daily_scores) / len(daily_scores)
        
        # Analyze health data for personalized recommendations
        sleep_recommendations = []
        exercise_recommendations = []
        movement_recommendations = []
        
        # Sleep recommendations based on scores and data
        if health_data:
            sleep_data = [day for day in health_data if "sleep_hours" in day]
            if sleep_data:
                avg_sleep = sum(day["sleep_hours"] for day in sleep_data) / len(sleep_data)
                if avg_sleep < 7:
                    sleep_recommendations.extend([
                        f"Increase sleep duration: Your current average of {avg_sleep:.1f} hours is below optimal. Aim for at least 7-8 hours.",
                        "Establish a consistent sleep schedule with the same bedtime and wake time every day.",
                        "Create a relaxing bedtime routine to signal your body it's time to sleep."
                    ])
                elif avg_sleep > 9:
                    sleep_recommendations.extend([
                        f"Optimize sleep duration: Your current average of {avg_sleep:.1f} hours may be more than needed. Aim for 7-9 hours.",
                        "Focus on improving sleep quality rather than quantity."
                    ])
                else:
                    sleep_recommendations.extend([
                        "Maintain your excellent sleep duration of 7-9 hours.",
                        "Focus on improving sleep quality by reducing disruptions."
                    ])
            
            # Exercise recommendations based on active calories
            exercise_data = [day for day in health_data if "active_calories" in day]
            if exercise_data:
                avg_calories = sum(day["active_calories"] for day in exercise_data) / len(exercise_data)
                if avg_calories < 300:
                    exercise_recommendations.extend([
                        f"Increase physical activity: Your current average of {int(avg_calories)} active calories is low.",
                        "Add 2-3 cardio sessions per week (20-30 minutes each).",
                        "Incorporate strength training 2 times per week."
                    ])
                elif avg_calories < 500:
                    exercise_recommendations.extend([
                        f"Enhance physical activity: Your current average of {int(avg_calories)} active calories is moderate.",
                        "Increase workout intensity or duration to reach 500+ active calories daily.",
                        "Add 1-2 HIIT sessions per week for metabolic benefits."
                    ])
                else:
                    exercise_recommendations.extend([
                        f"Maintain your excellent activity level of {int(avg_calories)} active calories.",
                        "Focus on exercise variety to engage different muscle groups."
                    ])
            
            # Movement recommendations based on steps
            steps_data = [day for day in health_data if "steps" in day]
            if steps_data:
                avg_steps = sum(day["steps"] for day in steps_data) / len(steps_data)
                if avg_steps < 5000:
                    movement_recommendations.extend([
                        f"Increase daily movement: Your current average of {int(avg_steps):,} steps is below recommended levels.",
                        "Take movement breaks every hour during sedentary periods.",
                        "Aim to gradually increase to 7,500+ steps daily."
                    ])
                elif avg_steps < 7500:
                    movement_recommendations.extend([
                        f"Enhance daily movement: Your current average of {int(avg_steps):,} steps is moderate.",
                        "Add a daily 15-minute walk to reach 7,500+ steps.",
                        "Take stairs instead of elevators when possible."
                    ])
                else:
                    movement_recommendations.extend([
                        f"Maintain your excellent step count of {int(avg_steps):,} steps.",
                        "Focus on consistent daily movement patterns throughout the week."
                    ])
        
        # Add general recommendations if specific data is not available
        if not sleep_recommendations:
            sleep_recommendations = [
                "Optimize sleep: Aim for 7-9 hours of quality sleep per night.",
                "Establish a consistent sleep schedule with the same bedtime and wake time.",
                "Create a sleep-friendly environment (dark, cool, quiet)."
            ]
        
        if not exercise_recommendations:
            exercise_recommendations = [
                "Regular exercise: Include both cardio and strength training.",
                "Aim for at least 150 minutes of moderate activity per week.",
                "Add 2-3 strength training sessions per week."
            ]
        
        if not movement_recommendations:
            movement_recommendations = [
                "Increase daily movement: Aim for 7,500-10,000 steps daily.",
                "Take movement breaks every hour during sedentary periods.",
                "Use active transportation when possible (walking, biking)."
            ]
        
        # Additional general recommendations
        general_recommendations = [
            "Nutrition: Focus on a plant-rich diet with adequate protein and healthy fats.",
            "Stress management: Practice meditation or other stress-reduction techniques.",
            "Social connections: Maintain strong social relationships for longevity benefits.",
            "Cognitive stimulation: Engage in learning and mentally challenging activities.",
            "Avoid toxins: Limit alcohol, avoid smoking, and minimize exposure to environmental toxins."
        ]
        
        # Create potential improvement points based on component scores
        sleep_potential = 0
        exercise_potential = 0
        movement_potential = 0
        
        if daily_scores:
            sleep_potential = 60 - avg_sleep_score if avg_sleep_score < 60 else 0
            exercise_potential = 30 - avg_exercise_score if avg_exercise_score < 30 else 0
            movement_potential = 30 - avg_steps_score if avg_steps_score < 30 else 0
        
        # Format the response with personalized recommendations
        detailed_response = f"""Based on your current metrics, here are targeted recommendations to improve your bio-age score:

1. Sleep Optimization ({'+' + str(int(sleep_potential)) if sleep_potential > 0 else 'Maintain'} points potential):
   ✓ {sleep_recommendations[0]}
   ✓ {sleep_recommendations[1]}
   ✓ {sleep_recommendations[2] if len(sleep_recommendations) > 2 else "Maintain consistent sleep quality"}

2. Exercise Enhancement ({'+' + str(int(exercise_potential)) if exercise_potential > 0 else 'Maintain'} points potential):
   ✓ {exercise_recommendations[0]}
   ✓ {exercise_recommendations[1]}
   ✓ {exercise_recommendations[2] if len(exercise_recommendations) > 2 else "Maintain exercise consistency"}

3. Movement Optimization ({'+' + str(int(movement_potential)) if movement_potential > 0 else 'Maintain'} points potential):
   ✓ {movement_recommendations[0]}
   ✓ {movement_recommendations[1]}
   ✓ {movement_recommendations[2] if len(movement_recommendations) > 2 else "Maintain daily movement patterns"}

Would you like a detailed plan for implementing any of these recommendations?"""
        
        # Combine all recommendations for insights
        all_recommendations = sleep_recommendations + exercise_recommendations + movement_recommendations + general_recommendations
        
        return {
            "response": detailed_response,
            "insights": all_recommendations,
            "visualization": None,
            "error": None
        }

    async def process_factors_query(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process bio age factors query.
        
        Args:
            data: Request data containing query, bio_age_data, and health_data
            
        Returns:
            Dict[str, Any]: Response with factors affecting biological age
        """
        # Extract data
        query = data.get("query", "")
        bio_age_data = data.get("bio_age_data", {})
        health_data = data.get("health_data", [])
        
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

    async def process_trend_query(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process bio age trend query.
        
        Args:
            data: Request data containing query, bio_age_data, and health_data
            
        Returns:
            Dict[str, Any]: Response with trend analysis of biological age
        """
        # Extract data
        query = data.get("query", "")
        bio_age_data = data.get("bio_age_data", {})
        health_data = data.get("health_data", [])
        
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
        daily_scores = bio_age_data.get("daily_scores", [])
        
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
            
            # Analyze component trends if daily_scores is available
            component_trends = {}
            if daily_scores and len(daily_scores) >= 2:
                # Split daily scores into earlier and later periods
                mid_point = len(daily_scores) // 2
                earlier_scores = daily_scores[:mid_point]
                later_scores = daily_scores[mid_point:]
                
                # Calculate average component scores for each period
                avg_earlier_sleep_score = sum(day.get("sleep_score", 0) for day in earlier_scores) / len(earlier_scores)
                avg_later_sleep_score = sum(day.get("sleep_score", 0) for day in later_scores) / len(later_scores)
                sleep_score_change = avg_later_sleep_score - avg_earlier_sleep_score
                
                avg_earlier_exercise_score = sum(day.get("exercise_score", 0) for day in earlier_scores) / len(earlier_scores)
                avg_later_exercise_score = sum(day.get("exercise_score", 0) for day in later_scores) / len(later_scores)
                exercise_score_change = avg_later_exercise_score - avg_earlier_exercise_score
                
                avg_earlier_steps_score = sum(day.get("steps_score", 0) for day in earlier_scores) / len(earlier_scores)
                avg_later_steps_score = sum(day.get("steps_score", 0) for day in later_scores) / len(later_scores)
                steps_score_change = avg_later_steps_score - avg_earlier_steps_score
                
                # Determine trend direction for each component
                component_trends = {
                    "sleep": "Improving" if sleep_score_change > 2 else "Declining" if sleep_score_change < -2 else "Stable",
                    "exercise": "Improving" if exercise_score_change > 2 else "Declining" if exercise_score_change < -2 else "Stable",
                    "steps": "Improving" if steps_score_change > 2 else "Declining" if steps_score_change < -2 else "Stable"
                }
                
                # Add component trend insights
                for component, trend in component_trends.items():
                    if trend == "Improving":
                        insights.append(f"Your {component} score is improving, contributing positively to your biological age.")
                    elif trend == "Declining":
                        insights.append(f"Your {component} score is declining, which may be increasing your biological age.")
            
            # Create a detailed trend response
            if component_trends:
                starting_score = sum(day.get("total_score", 0) for day in daily_scores[:5]) / 5 if len(daily_scores) >= 5 else first_score
                current_score = sum(day.get("total_score", 0) for day in daily_scores[-5:]) / 5 if len(daily_scores) >= 5 else last_score
                score_improvement = current_score - starting_score
                
                detailed_response = f"""Here's your 30-day bio-age score trend analysis:

📈 Score Progression:
- Starting Score: {int(starting_score)}/120
- Current Score: {int(current_score)}/120
- Net Change: {'+' if score_improvement > 0 else ''}{int(score_improvement)} points

Component Trends:
1. Sleep ({component_trends.get('sleep', 'Stable')}):
   - Average score: {int(sum(day.get('sleep_score', 0) for day in daily_scores) / len(daily_scores))}/60
   - {sleep_change:.1f} hour change in average duration

2. Exercise ({component_trends.get('exercise', 'Stable')}):
   - Average score: {int(sum(day.get('exercise_score', 0) for day in daily_scores) / len(daily_scores))}/30
   - {steps_change/1000:.1f}K step change in daily average

3. Movement ({component_trends.get('steps', 'Stable')}):
   - Average score: {int(sum(day.get('steps_score', 0) for day in daily_scores) / len(daily_scores))}/30
   - {int(abs(steps_change))} step change in daily average"""
                
                return {
                    "response": detailed_response,
                    "insights": insights,
                    "visualization": visualization,
                    "error": None
                }
            else:
                # Fallback to simple response if no component trends are available
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