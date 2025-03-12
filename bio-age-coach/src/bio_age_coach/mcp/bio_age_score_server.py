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
from .base import BaseMCPServer

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
                raise ValueError(f"Expected dictionary, got {type(health_data)}")
            
            score = 0
            score_breakdown = {}
            insights = []
            
            # Sleep score (max 60 points)
            sleep_hours = float(health_data.get('sleep_hours', 0))
            if sleep_hours >= 8.5:
                sleep_score = 60
                insights.append("Optimal sleep duration achieved - associated with 2-3 year reduction in biological age")
            elif sleep_hours >= 7.0:
                sleep_score = 50
                insights.append("Good sleep duration - maintaining 7+ hours consistently recommended")
            else:
                sleep_score = (sleep_hours / 7.0) * 50
                insights.append("Sleep duration below recommended 7-9 hours - consider sleep hygiene improvements")
            score += sleep_score
            score_breakdown['sleep_score'] = sleep_score
            
            # Exercise score (max 30 points)
            active_calories = float(health_data.get('active_calories', 0))
            if active_calories >= 750:
                exercise_score = 30
                insights.append("Excellent activity level - associated with 4-5 year reduction in biological age")
            elif active_calories >= 500:
                exercise_score = 20
                insights.append("Good activity level - maintaining 500+ active calories recommended")
            elif active_calories >= 350:
                exercise_score = 10
                insights.append("Moderate activity - increasing to 500+ active calories suggested")
            else:
                exercise_score = (active_calories / 350) * 10
                insights.append("Activity level below recommendations - consider increasing daily movement")
            score += exercise_score
            score_breakdown['exercise_score'] = exercise_score
            
            # Steps score (max 30 points)
            steps = float(health_data.get('steps', 0))
            if steps >= 10000:
                steps_score = 30
                insights.append("Optimal step count achieved - associated with increased longevity")
            elif steps >= 7500:
                steps_score = 20
                insights.append("Good step count - maintaining 7,500+ steps recommended")
            elif steps >= 5000:
                steps_score = 10
                insights.append("Moderate step count - increasing to 7,500+ steps suggested")
            else:
                steps_score = (steps / 5000) * 10
                insights.append("Step count below recommendations - consider ways to increase daily steps")
            score += steps_score
            score_breakdown['steps_score'] = steps_score
            
            score_breakdown['total_score'] = score
            score_breakdown['insights'] = insights
            score_breakdown['date'] = health_data.get('date')
            return score_breakdown
            
        except Exception as e:
            print(f"Error calculating daily score: {str(e)}")
            return {
                'total_score': 0,
                'sleep_score': 0,
                'exercise_score': 0,
                'steps_score': 0,
                'insights': [f"Error calculating score: {str(e)}"],
                'date': health_data.get('date') if isinstance(health_data, dict) else None
            }
    
    async def calculate_30_day_scores(self, health_data_series: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Calculate bio age scores for the last 30 days.
        
        Args:
            health_data_series: List of daily health data dictionaries
            
        Returns:
            List of daily scores with breakdowns and trend analysis
        """
        try:
            if not isinstance(health_data_series, list):
                raise ValueError(f"Expected list, got {type(health_data_series)}")
            
            scores = []
            for daily_data in health_data_series:
                if not isinstance(daily_data, dict):
                    raise ValueError(f"Expected dictionary for daily data, got {type(daily_data)}")
                score_data = await self.calculate_daily_score(daily_data)
                scores.append(score_data)
                
            # Add trend analysis
            if len(scores) >= 7:
                recent_scores = pd.DataFrame(scores[-7:])
                trend = {
                    'sleep_trend': recent_scores['sleep_score'].mean(),
                    'exercise_trend': recent_scores['exercise_score'].mean(),
                    'steps_trend': recent_scores['steps_score'].mean(),
                    'total_trend': recent_scores['total_score'].mean()
                }
                scores.append({'trend_analysis': trend})
            
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
        
    async def _process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming requests based on request type."""
        try:
            request_type = request.get("type", "")
            user_data = request.get("data", {})
            health_data = user_data.get("health_data", [])
            
            if request_type == "calculate_daily_score":
                # Calculate daily score from metrics
                metrics = request.get("metrics", {})
                if not metrics and isinstance(health_data, list) and health_data:
                    # Use latest health data if metrics not provided
                    metrics = health_data[-1]
                score = await self.calculate_daily_score(metrics)
                return {
                    "total_score": score.get("total_score", 0),
                    "sleep_score": score.get("sleep_score", 0),
                    "exercise_score": score.get("exercise_score", 0),
                    "steps_score": score.get("steps_score", 0),
                    "insights": score.get("insights", [])
                }
                
            elif request_type == "calculate_30_day_scores":
                # Calculate scores for last 30 days
                if isinstance(health_data, list) and health_data:
                    scores = await self.calculate_30_day_scores(health_data)
                    return {
                        "scores": scores[:-1] if scores and isinstance(scores[-1], dict) and "trend_analysis" in scores[-1] else scores,
                        "trends": scores[-1].get("trend_analysis", {}) if scores and isinstance(scores[-1], dict) and "trend_analysis" in scores[-1] else {},
                        "insights": [s.get("insights", []) for s in scores if "insights" in s]
                    }
                else:
                    return {"error": "No health data available for 30-day score calculation"}
                    
            elif request_type == "visualization":
                # Create visualization of scores
                if isinstance(health_data, list) and health_data:
                    # Calculate scores first
                    scores = await self.calculate_30_day_scores(health_data)
                    if not scores:
                        return {"error": "No scores available for visualization"}
                    
                    # Create visualization
                    visualization = await self.create_score_visualization(scores[:-1] if scores and isinstance(scores[-1], dict) and "trend_analysis" in scores[-1] else scores)
                    return {
                        "visualization": visualization,
                        "scores": scores[:-1] if scores and isinstance(scores[-1], dict) and "trend_analysis" in scores[-1] else scores,
                        "trends": scores[-1].get("trend_analysis", {}) if scores and isinstance(scores[-1], dict) and "trend_analysis" in scores[-1] else {},
                        "insights": [s.get("insights", []) for s in scores if "insights" in s]
                    }
                else:
                    return {"error": "No health data available for visualization"}
                    
            elif request_type == "store_habits":
                # Store user habits
                user_id = request.get("user_id", "test_user")
                habits = request.get("habits", {})
                await self.store_habits_beliefs(user_id, habits)
                self.user_habits = habits
                return {"status": "success", "message": "Habits stored successfully"}
                
            elif request_type == "store_plan":
                # Store user plan
                user_id = request.get("user_id", "test_user")
                plan = request.get("plan", {})
                await self.store_user_plan(user_id, plan)
                self.user_plan = plan
                return {"status": "success", "message": "Plan stored successfully"}
                
            elif request_type == "get_habits":
                # Retrieve user habits
                user_id = request.get("user_id", "test_user")
                habits = await self.get_habits_beliefs(user_id) or self.user_habits
                return {"habits": habits} if habits else {"error": "No habits found"}
                
            elif request_type == "get_plan":
                # Retrieve user plan
                user_id = request.get("user_id", "test_user")
                plan = await self.get_user_plan(user_id) or self.user_plan
                return {"plan": plan} if plan else {"error": "No plan found"}
                
            elif request_type == "query":
                # Process general query about bio age score
                query = request.get("query", "")
                if isinstance(health_data, list) and health_data:
                    # Calculate scores and insights
                    scores = await self.calculate_30_day_scores(health_data)
                    visualization = await self.create_score_visualization(scores[:-1] if scores and isinstance(scores[-1], dict) and "trend_analysis" in scores[-1] else scores)
                    return {
                        "scores": scores[:-1] if scores and isinstance(scores[-1], dict) and "trend_analysis" in scores[-1] else scores,
                        "trends": scores[-1].get("trend_analysis", {}) if scores and isinstance(scores[-1], dict) and "trend_analysis" in scores[-1] else {},
                        "visualization": visualization,
                        "insights": [s.get("insights", []) for s in scores if "insights" in s],
                        "habits": self.user_habits,
                        "plan": self.user_plan
                    }
                else:
                    return {"error": "No health data available for analysis"}
            
            else:
                return {"error": f"Unknown request type: {request_type}"}
                
        except Exception as e:
            print(f"Error processing request: {str(e)}")
            return {"error": f"Error processing request: {str(e)}"}
            
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