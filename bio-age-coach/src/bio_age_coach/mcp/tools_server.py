"""
Tools server implementation for processing tool-specific requests.
"""

from typing import Dict, Any, Optional
import aiohttp
from .base import BaseMCPServer
import os
import json

class ToolsServer(BaseMCPServer):
    """Server for managing fitness metrics and other tools."""
    
    def __init__(self, api_key: str, data_path: str = "data/tools"):
        """Initialize the tools server."""
        super().__init__(api_key)
        self.data_path = data_path
        self.session: Optional[aiohttp.ClientSession] = None
        self.config: Dict[str, Any] = {
            "tools": ["biological_age", "health_score", "fitness_metrics", "analyze"],
            "fitness_metrics": {},
            "tool_name": "tools"  # Add default tool name
        }
        self.fitness_metrics: Dict[str, Any] = {}
        self.data_dir = data_path
        self.config_file = os.path.join(self.data_dir, "tools_config.json")
        os.makedirs(self.data_path, exist_ok=True)
        
        # Load initial configuration
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from file."""
        try:
            config_path = os.path.join(self.data_path, "tools_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    file_config = json.load(f)
                    # Update config while preserving tools field
                    self.config.update(file_config)
                    if "fitness_metrics" in file_config:
                        self.fitness_metrics = file_config["fitness_metrics"]
        except Exception as e:
            print(f"Error loading tools config: {str(e)}")

    async def initialize_data(self, data: Dict[str, Any]) -> None:
        """Initialize server with test data."""
        from bio_age_coach.types import DataCategory
        
        if DataCategory.FITNESS_METRICS.value in data:
            fitness_data = data[DataCategory.FITNESS_METRICS.value]
            self.fitness_metrics = fitness_data
            self.config["fitness_metrics"] = self.fitness_metrics
                
            # Save the updated config
            try:
                with open(self.config_file, "w") as f:
                    json.dump(self.config, f, indent=4)
            except Exception as e:
                print(f"Error saving tools config: {str(e)}")

    async def _process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming requests."""
        if not await self.authenticate(request):
            return {"error": "Authentication failed"}

        request_type = request.get("type", "")
        
        if request_type == "get_config":
            return {"config": await self.get_config()}
        elif request_type == "query":
            tool_name = request.get("tool_name", "")
            if not tool_name:
                return {"error": "tool_name is required"}
            if tool_name not in ["biological_age", "health_score", "fitness_metrics", "analyze"]:
                return {"error": f"Unknown tool: {tool_name}"}
            return {"result": await self.process_query(request)}
        else:
            return {"error": f"Unknown request type: {request_type}"}

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming requests."""
        return await self._process_request(request)

    async def get_config(self) -> Dict[str, Any]:
        """Get the current server configuration."""
        return self.config

    async def process_query(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process a query request."""
        tool_name = request.get("tool_name", "")
        data = request.get("data", {})
        
        if tool_name == "biological_age":
            return await self._calculate_biological_age(data)
        elif tool_name == "health_score":
            return await self._calculate_health_score(data)
        elif tool_name == "fitness_metrics":
            return await self._get_fitness_metrics()
        elif tool_name == "analyze":
            return await self._analyze_data(data)
        else:
            return {"error": f"Unknown tool: {tool_name}"}

    async def _calculate_biological_age(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate biological age based on health metrics."""
        # Validate inputs
        age = data.get("chronological_age", 35)
        heart_rate = data.get("resting_heart_rate", 70)
        active_calories = data.get("active_calories", 300)
        steps = data.get("steps", 7000)
        sleep = data.get("sleep_hours", 7)

        # Simple calculation (this is just a placeholder)
        bio_age = age
        if heart_rate < 60:
            bio_age -= 2
        elif heart_rate > 80:
            bio_age += 2

        if active_calories > 400:
            bio_age -= 1
        elif active_calories < 200:
            bio_age += 1

        if steps > 10000:
            bio_age -= 1
        elif steps < 5000:
            bio_age += 1

        if sleep >= 7 and sleep <= 9:
            bio_age -= 1
        else:
            bio_age += 1

        return {
            "tool_name": "biological_age",
            "chronological_age": age,
            "biological_age": bio_age,
            "factors": {
                "heart_rate": heart_rate,
                "active_calories": active_calories,
                "steps": steps,
                "sleep": sleep
            }
        }

    async def _calculate_health_score(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate health score based on available metrics."""
        # Validate inputs
        heart_rate = data.get("resting_heart_rate", 70)
        active_calories = data.get("active_calories", 300)
        steps = data.get("steps", 7000)
        sleep = data.get("sleep_hours", 7)

        # Simple scoring (this is just a placeholder)
        heart_score = 90 if heart_rate < 70 else 80
        activity_score = 90 if active_calories > 350 else 80
        steps_score = 90 if steps > 8000 else 80
        sleep_score = 90 if sleep >= 7 else 80

        overall_score = (heart_score + activity_score + steps_score + sleep_score) / 4

        return {
            "tool_name": "health_score",
            "health_score": overall_score,
            "components": {
                "heart_rate": heart_score,
                "activity": activity_score,
                "steps": steps_score,
                "sleep": sleep_score
            }
        }

    async def _get_fitness_metrics(self) -> Dict[str, Any]:
        """Get fitness metrics configuration."""
        return {
            "tool_name": "fitness_metrics",
            "metrics": self.fitness_metrics
        }
        
    async def _analyze_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze provided data."""
        metrics = data.get("metrics", {})
        analysis = {}
        
        for metric, values in metrics.items():
            if isinstance(values, list) and values:
                avg = sum(values) / len(values)
                trend = "increasing" if values[-1] > values[0] else "decreasing" if values[-1] < values[0] else "stable"
                analysis[metric] = {
                    "average": avg,
                    "trend": trend,
                    "min": min(values),
                    "max": max(values)
                }
        
        return {
            "tool_name": "analyze",
            "analysis": analysis
        }

    async def run_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run a specific tool with parameters."""
        if tool_name == "fitness_metrics":
            return await self.process_fitness_metrics(params)
        elif tool_name == "query":
            return await self.process_query(params)
        else:
            return {"error": f"Unknown tool: {tool_name}"}

    async def process_fitness_metrics(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Process fitness metrics request."""
        metrics = await self._get_fitness_metrics()
        return {
            "tool_name": "fitness_metrics",
            "fitness_metrics": metrics
        }

    async def close(self) -> None:
        """Close any open connections."""
        if self.session:
            await self.session.close() 