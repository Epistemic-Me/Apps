"""
Health server implementation for managing user health data.
"""

import json
import os
import csv
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import aiofiles
import aiohttp
from .base import BaseMCPServer
from bio_age_coach.types import DataCategory

class HealthServer(BaseMCPServer):
    """Server for managing user health data."""
    
    def __init__(self, api_key: str, data_path: str = None):
        """Initialize the health server."""
        super().__init__(api_key)
        self.data_path = data_path
        self.test_data_path = os.path.join(os.path.dirname(__file__), "..", "..", "test_health_data") if data_path is None else data_path
        self.users = {}  # Dictionary to store user data
        self.processed_health_data = {
            "workouts": [],
            "daily_metrics": {
                "steps": [],
                "active_calories": [],
                "heart_rate": [],
                "distance": []
            },
            "aggregated_metrics": {}
        }
        
    async def initialize_data(self, data: Dict[str, Any]) -> None:
        """Initialize server with test data."""
        if "users" in data:
            self.users = {user["id"]: user for user in data["users"]}
        
        if DataCategory.HEALTH_METRICS.value in data:
            health_metrics = data[DataCategory.HEALTH_METRICS.value]
            self.users["test_user"] = {
                "health_data": health_metrics
            }
            self.processed_health_data = health_metrics
            
        if "biomarkers" in data:
            if "test_user" not in self.users:
                self.users["test_user"] = {}
            self.users["test_user"]["biomarkers"] = data["biomarkers"]
        
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

    def _process_apple_health_data(self) -> None:
        """Process Apple Health CSV files and aggregate the data."""
        if not os.path.exists(self.test_data_path):
            print(f"Test data directory not found: {self.test_data_path}")
            return

        # Initialize data structures
        self.processed_health_data = {
            "workouts": [],
            "daily_metrics": {
                "steps": [],
                "active_calories": [],
                "heart_rate": [],
                "distance": []
            },
            "aggregated_metrics": {}
        }

        # Process workout summary file
        workout_summary_file = os.path.join(self.test_data_path, "Workouts-20250205_000000-20250307_235959.csv")
        if os.path.exists(workout_summary_file):
            try:
                df = pd.read_csv(workout_summary_file)
                self.processed_health_data["workouts"] = df.to_dict('records')
            except Exception as e:
                print(f"Error processing workout summary file: {str(e)}")

        # Process individual workout files
        for file in os.listdir(self.test_data_path):
            if file.endswith('.csv') and not file.startswith('Workouts-'):
                file_path = os.path.join(self.test_data_path, file)
                try:
                    # Extract metric type from filename
                    parts = file.split('-')
                    if len(parts) >= 2:
                        metric_type = parts[1].replace('.csv', '')
                        normalized_metric = self._normalize_metric_name(metric_type)

                        if normalized_metric in self.processed_health_data["daily_metrics"]:
                            # Read and process the CSV file
                            df = pd.read_csv(file_path)
                            if not df.empty and 'value' in df.columns:
                                self.processed_health_data["daily_metrics"][normalized_metric].extend(df.to_dict('records'))

                except Exception as e:
                    print(f"Error processing file {file}: {str(e)}")

        # Aggregate daily metrics
        self._aggregate_metrics()

    def _aggregate_metrics(self) -> None:
        """Aggregate daily metrics from processed health data."""
        metrics = {
            "steps": {"total": 0, "avg": 0, "min": None, "max": 0},
            "active_calories": {"total": 0, "avg": 0, "min": None, "max": 0},
            "heart_rate": {"avg": 0, "min": None, "max": 0},
            "distance": {"total": 0, "avg": 0, "min": None, "max": 0}
        }

        # Process each metric type
        daily_metrics = self.processed_health_data.get("daily_metrics", {})
        for metric_type in ["steps", "active_calories", "heart_rate", "distance"]:
            data = daily_metrics.get(metric_type, [])
            if not data:
                continue

            try:
                df = pd.DataFrame(data)
                if 'value' in df.columns and not df.empty:
                    values = df['value'].dropna()
                    if not values.empty:
                        metrics[metric_type] = {
                            "total": float(values.sum()),
                            "avg": float(values.mean()),
                            "min": float(values.min()),
                            "max": float(values.max())
                        }
            except Exception as e:
                print(f"Error aggregating metrics for {metric_type}: {str(e)}")
                continue

        self.processed_health_data["aggregated_metrics"] = metrics
            
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
            
    async def _process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming requests."""
        if not await self.authenticate(request):
            return {"error": "Authentication failed"}

        request_type = request.get("type", "")
        
        if request_type == "user_data":
            if "user_id" not in request:
                return {"error": "user_id is required"}
            user_data = await self.get_user_data(request["user_id"])
            if "error" in user_data:
                return user_data
            return {"health_data": user_data.get("health_data", {})}
            
        elif request_type == "update":
            if "user_id" not in request or "data" not in request:
                return {"error": "user_id and data are required"}
            await self.update_user_data(request["user_id"], request["data"])
            return {"status": "success"}
            
        elif request_type == "users":
            users = await self.get_users()
            return {"users": users}
            
        elif request_type == "trends":
            if "user_id" not in request:
                return {"error": "user_id is required"}
            trends = await self.get_trends(request["user_id"])
            if "error" in trends:
                return trends
            return {"trends": trends}

        elif request_type == "metrics":
            timeframe = request.get("timeframe", "1D")
            metrics = await self.get_metrics(timeframe)
            return {"metrics": metrics}
            
        else:
            return {"error": f"Unknown request type: {request_type}"}
            
    async def close(self) -> None:
        """Close any open connections."""
        pass 