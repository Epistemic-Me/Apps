"""
Health Server for processing and managing health data from Apple Health.
"""

import json
import os
import csv
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import aiofiles
import aiohttp
from ..core.base import BaseMCPServer
from bio_age_coach.types import DataCategory

class HealthServer(BaseMCPServer):
    """Server for processing and managing health data."""
    
    def __init__(self, api_key: str, data_dir: str = None):
        """Initialize the Health Server.
        
        Args:
            api_key: API key for authentication
            data_dir: Optional directory for test data
        """
        super().__init__(api_key)
        self.test_data_path = data_dir
        self.processed_health_data = {
            "metrics": {},
            "workouts": []
        }
        self.users = {}
        
        # Initialize MCP resources and tools
        self._initialize_resources()
        self._initialize_tools()
    
    def _initialize_resources(self) -> None:
        """Initialize MCP resources for health data."""
        self.resources = {
            "workouts": {
                "uri": "health://data/workouts",
                "name": "Workout Data",
                "description": "User's workout data from Apple Health",
                "mimeType": "application/json"
            },
            "daily_metrics": {
                "uri": "health://data/daily_metrics",
                "name": "Daily Health Metrics",
                "description": "Aggregated daily health metrics",
                "mimeType": "application/json"
            },
            "heart_rate": {
                "uri": "health://data/heart_rate",
                "name": "Heart Rate Data",
                "description": "User's heart rate measurements",
                "mimeType": "application/json"
            }
        }
        
        # Resource templates for dynamic data
        self.resource_templates = {
            "workout_by_date": {
                "uriTemplate": "health://data/workouts/{date}",
                "name": "Workout by Date",
                "description": "Workout data for a specific date",
                "mimeType": "application/json"
            },
            "metrics_by_date": {
                "uriTemplate": "health://data/metrics/{date}",
                "name": "Metrics by Date",
                "description": "Health metrics for a specific date",
                "mimeType": "application/json"
            }
        }
    
    def _initialize_tools(self) -> None:
        """Initialize MCP tools for health data processing."""
        self.tools = {
            "process_workout_data": {
                "name": "process_workout_data",
                "description": "Process workout data from Apple Health export",
                "parameters": {
                    "data_dir": {"type": "string"}
                },
                "function": self.process_workout_data
            },
            "aggregate_metrics": {
                "name": "aggregate_metrics",
                "description": "Aggregate health metrics by date",
                "parameters": {
                    "metrics": {
                        "type": "object",
                        "properties": {
                            "workouts": {"type": "array"}
                        }
                    }
                },
                "function": self._aggregate_metrics
            }
        }
    
    async def _process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming requests."""
        try:
            request_type = request.get("type", "")
            
            # Handle resource requests
            if request_type == "resources/list":
                return {
                    "resources": list(self.resources.values()),
                    "resourceTemplates": list(self.resource_templates.values())
                }
            
            elif request_type == "resources/read":
                uri = request.get("uri", "")
                if uri.startswith("health://data/workouts/"):
                    # Extract date from URI
                    date = uri.split("/")[-1]
                    # Find workouts for this date
                    workouts = []
                    for workout in self.processed_health_data.get("workouts", []):
                        if isinstance(workout, dict) and "date" in workout:
                            if workout["date"] == date:
                                workouts.append(workout)
                    return {
                        "contents": [{
                            "uri": uri,
                            "mimeType": "application/json",
                            "text": str(workouts)
                        }]
                    }
                return await self._read_resource(uri)
            
            # Handle data initialization
            elif request_type == "initialize_data":
                data = request.get("data", {})
                if "test_data_path" in data:
                    self.test_data_path = data["test_data_path"]
                if "metrics" in data:
                    metrics = data["metrics"]
                    if isinstance(metrics, dict):
                        # Convert dict to list format
                        metrics_list = []
                        for date, values in metrics.items():
                            metric_entry = {"date": date, **values}
                            metrics_list.append(metric_entry)
                        self.processed_health_data["metrics"] = metrics_list
                    else:
                        self.processed_health_data["metrics"] = metrics
                return {"status": "success"}
            
            # Handle workout data processing
            elif request_type == "process_workout_data":
                data_dir = request.get("data", {}).get("data_dir", "")
                if data_dir:
                    self.test_data_path = data_dir
                workouts = await self.process_workout_data(self.test_data_path)
                self.processed_health_data["workouts"] = workouts
                return workouts
            
            # Handle metrics request
            elif request_type == "metrics":
                if not self.processed_health_data:
                    return {"error": "No health data available"}
                metrics = self.processed_health_data.get("metrics", [])
                if isinstance(metrics, dict):
                    # Convert dict to list format
                    metrics_list = []
                    for date, values in metrics.items():
                        metric_entry = {"date": date, **values}
                        metrics_list.append(metric_entry)
                    metrics = metrics_list
                return {
                    "metrics": metrics,
                    "workouts": self.processed_health_data.get("workouts", [])
                }
            
            # Handle aggregate metrics request
            elif request_type == "aggregate_metrics":
                data = request.get("data", {})
                metrics = data.get("metrics", {})
                if not metrics:
                    return {"error": "No metrics provided"}
                aggregated = await self._aggregate_metrics(metrics)
                return {"metrics": aggregated}
            
            else:
                return {"error": f"Unknown request type: {request_type}"}
                
        except Exception as e:
            print(f"Error processing request: {str(e)}")
            return {"error": f"Error processing request: {str(e)}"}
    
    async def _read_resource(self, uri: str) -> Dict[str, Any]:
        """Read a resource by URI."""
        try:
            if uri == "health://data/workouts":
                return {
                    "contents": [{
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": str(self.processed_health_data["workouts"])
                    }]
                }
            elif uri == "health://data/daily_metrics":
                return {
                    "contents": [{
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": str(self.processed_health_data["metrics"])
                    }]
                }
            elif uri.startswith("health://data/workouts/"):
                date = uri.split("/")[-1]
                workouts = []
                for workout in self.processed_health_data["workouts"]:
                    workout_date = workout["date"]
                    if workout_date == date:
                        workouts.append(workout)
                return {
                    "contents": [{
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": str(workouts)
                    }]
                }
            elif uri.startswith("health://data/metrics/"):
                date = uri.split("/")[-1]
                metrics = None
                if isinstance(self.processed_health_data["metrics"], list):
                    metrics = next((m for m in self.processed_health_data["metrics"] if m["date"] == date), {})
                else:
                    metrics = self.processed_health_data["metrics"].get(date, {})
                return {
                    "contents": [{
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": str(metrics)
                    }]
                }
            
            return {"error": f"Resource not found: {uri}"}
            
        except Exception as e:
            print(f"Error reading resource: {str(e)}")
            return {"error": f"Error reading resource: {str(e)}"}
    
    def _generate_test_data(self) -> List[Dict[str, Any]]:
        """Generate realistic test data with various patterns."""
        today = datetime.now()
        daily_metrics = []
        
        # Define patterns for more realistic data
        patterns = [
            {"name": "consistent", "sleep": (7.5, 8.5), "calories": (400, 600), "steps": (9000, 11000), "heart_rate": (65, 75)},
            {"name": "improving", "sleep": (6.0, 8.0), "calories": (300, 700), "steps": (7000, 12000), "heart_rate": (60, 80)},
            {"name": "declining", "sleep": (8.0, 6.0), "calories": (600, 300), "steps": (11000, 7000), "heart_rate": (70, 65)},
            {"name": "weekend_dip", "sleep": [(7.5, 8.5), (6.0, 7.0)], "calories": [(500, 600), (300, 400)], "steps": [(10000, 11000), (6000, 7000)], "heart_rate": [(65, 75), (70, 80)]}
        ]
        
        # Generate 30 days of data with patterns
        for i in range(30):
            date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            pattern = patterns[i % len(patterns)]
            
            # Apply pattern with some randomness
            if isinstance(pattern["sleep"], tuple):
                sleep_range = pattern["sleep"]
                calories_range = pattern["calories"]
                steps_range = pattern["steps"]
                heart_rate_range = pattern["heart_rate"]
            else:
                # Weekend pattern
                is_weekend = i % 7 >= 5
                idx = 1 if is_weekend else 0
                sleep_range = pattern["sleep"][idx]
                calories_range = pattern["calories"][idx]
                steps_range = pattern["steps"][idx]
                heart_rate_range = pattern["heart_rate"][idx]
            
            import random
            metrics = {
                "date": date,
                "active_calories": round(random.uniform(*calories_range)),
                "steps": round(random.uniform(*steps_range)),
                "heart_rate": round(random.uniform(*heart_rate_range)),
                "sleep_hours": round(random.uniform(*sleep_range), 1),
                "workout_count": 1 if random.random() > 0.2 else 0  # 80% chance of having a workout
            }
            daily_metrics.append(metrics)
        
        return sorted(daily_metrics, key=lambda x: x["date"])

    async def _process_apple_health_data(self) -> None:
        """Process Apple Health data from test directory."""
        try:
            if not self.test_data_path or not os.path.exists(self.test_data_path):
                print(f"Test data directory not found: {self.test_data_path}")
                return
            
            # Generate test data
            daily_metrics = self._generate_test_data()
            
            # Create workout data from daily metrics
            workouts = []
            for metrics in daily_metrics:
                if metrics["workout_count"] > 0:
                    workout = {
                        "date": metrics["date"],
                        "active_calories": metrics["active_calories"],
                        "steps": metrics["steps"],
                        "heart_rate": metrics["heart_rate"],
                        "sleep_hours": metrics["sleep_hours"],
                        "workout_count": metrics["workout_count"]
                    }
                    workouts.append(workout)
            
            # Store processed data
            self.processed_health_data = {
                "metrics": daily_metrics,
                "workouts": workouts
            }
            
            print(f"Generated {len(daily_metrics)} days of health data")
            print(f"Generated {len(workouts)} workouts")
                
        except Exception as e:
            print(f"Error processing Apple Health data: {str(e)}")
            import traceback
            traceback.print_exc()
    
    async def _aggregate_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate health metrics by date."""
        try:
            workouts = metrics.get("workouts", [])
            if not workouts:
                return {}
            
            aggregated = {}
            for workout in workouts:
                date = workout.get("date")
                if not date:
                    continue
                
                if date not in aggregated:
                    aggregated[date] = {
                        "active_calories": 0,
                        "steps": 0,
                        "heart_rate": 0,
                        "workout_count": 0,
                        "total_heart_rate": 0  # Track total heart rate for averaging
                    }
                
                # Sum up metrics
                aggregated[date]["active_calories"] += workout.get("active_calories", 0)
                aggregated[date]["steps"] += workout.get("steps", 0)
                aggregated[date]["total_heart_rate"] += workout.get("heart_rate", 0)  # Add to total
                aggregated[date]["workout_count"] += 1
            
            # Calculate average heart rate for each date
            for date_metrics in aggregated.values():
                if date_metrics["workout_count"] > 0:
                    date_metrics["heart_rate"] = date_metrics["total_heart_rate"] / date_metrics["workout_count"]
                del date_metrics["total_heart_rate"]  # Remove the total from the final output
            
            return aggregated
            
        except Exception as e:
            print(f"Error aggregating metrics: {str(e)}")
            return {}
    
    async def process_workout_data(self, data_dir: str) -> List[Dict[str, Any]]:
        """Process workout data from CSV files."""
        try:
            # Read workout data
            workout_file = os.path.join(data_dir, "Workouts-20240301_000000-20240301_235959.csv")
            df = pd.read_csv(workout_file)
            
            # Convert date column to datetime
            df['date'] = pd.to_datetime(df['date'])
            
            # Group by date and calculate daily metrics
            daily_metrics = []
            for date, group in df.groupby('date'):
                # Calculate total active calories (sum of all workouts)
                active_calories = group['active_calories'].sum()
                
                # Calculate total steps (sum of all workouts)
                steps = group['steps'].sum()
                
                # Calculate average heart rate (weighted by workout duration)
                weighted_hr = ((group['heart_rate'] * group['workout_count']).sum() / group['workout_count'].sum()) if not group['workout_count'].empty else 0
                
                # Create daily metrics entry
                metrics = {
                    'date': date.strftime('%Y-%m-%d'),
                    'active_calories': float(active_calories),
                    'steps': float(steps),
                    'heart_rate': float(weighted_hr),
                    'workout_count': int(group['workout_count'].sum())
                }
                daily_metrics.append(metrics)
            
            # Sort by date
            daily_metrics = sorted(daily_metrics, key=lambda x: x['date'])
            
            return daily_metrics
            
        except Exception as e:
            print(f"Error processing workout data: {str(e)}")
            return []

    def _ensure_data_directory(self) -> None:
        """Ensure the data directory exists."""
        os.makedirs(self.data_path, exist_ok=True)
        
    def _ensure_users_file(self) -> None:
        """Ensure the users file exists and load users data."""
        users_file = os.path.join(self.data_path, "users.json")
        if not os.path.exists(users_file):
            with open(users_file, 'w') as f:
                json.dump({"users": {}}, f)
        else:
            with open(users_file, 'r') as f:
                data = json.load(f)
                self.users = data.get("users", {})
                
    def _normalize_metric_name(self, metric_name: str) -> str:
        """Normalize metric names to consistent format."""
        # Map of raw metric names to normalized ones
        metric_map = {
            'Active Energy': 'active_calories',
            'Step Count': 'steps',
            'Heart Rate': 'heart_rate',
            'Walking + Running Distance': 'distance',
            'Walking Distance': 'distance',
            'Running Distance': 'distance'
        }
        return metric_map.get(metric_name, metric_name.lower().replace(' ', '_').replace('+', '_'))

    async def _get_health_metrics(self, timeframe: str) -> Dict[str, Any]:
        """Get health metrics for a specific timeframe."""
        # For now, return test data
        return {
            "active_calories": 400,
            "steps": 8000,
            "heart_rate": 65,
            "sleep_hours": 7.5
        }
        
    async def _get_health_trends(self, metric: str) -> Dict[str, Any]:
        """Get health trends for a specific metric."""
        # For now, return test data
        return {
            "trends": [
                {"date": "2024-03-01", "value": 8000},
                {"date": "2024-03-02", "value": 9000},
                {"date": "2024-03-03", "value": 10000}
            ]
        }
        
    async def get_user_data(self, user_id: str) -> Dict[str, Any]:
        """Get user data."""
        return self.users.get(user_id, {})
            
    async def update_user_data(self, user_id: str, data: Dict[str, Any]) -> None:
        """Update user data."""
        if user_id not in self.users:
            self.users[user_id] = {}
        self.users[user_id].update(data)
            
    async def get_users(self) -> Dict[str, Any]:
        """Get list of users."""
        return {"users": [{"id": user_id, "username": user.get("username", user_id)} 
                        for user_id, user in self.users.items()]}
            
    async def get_trends(self, user_id: str) -> Dict[str, Any]:
        """Get health trends for a user."""
        if user_id not in self.users:
            return {"error": "User not found"}
        
        user_data = self.users[user_id]
        if "health_data" not in user_data:
            return {"error": "No health data found"}
        
        health_data = user_data["health_data"]
        trends = {}
        
        # Calculate trends for each metric
        for metric in ["steps", "active_calories", "heart_rate", "sleep_hours"]:
            if metric in health_data:
                trends[metric] = {
                    "current": health_data[metric],
                    "trend": "stable"  # Placeholder, would calculate from historical data
                }
        
        return trends
            
    async def get_metrics(self, timeframe: str = "1D") -> Dict[str, Any]:
        """Get health metrics for a timeframe."""
        # For now, just return the processed health data
        return self.processed_health_data
            
    async def close(self) -> None:
        """Close any open connections."""
        pass 