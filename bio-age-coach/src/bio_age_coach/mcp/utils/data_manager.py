"""
Data manager for MCP servers.
"""

import os
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
import pandas as pd
from ..servers.health_server import HealthServer
from ..servers.research_server import ResearchServer
from ..servers.tools_server import ToolsServer
from ..types import DataCategory
from datetime import datetime

class MCPDataManager:
    """Manages data initialization and updates for MCP servers."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.health_data_dir = self.data_dir / "health"
        self.research_data_dir = self.data_dir / "research"
        self.tools_data_dir = self.data_dir / "tools"
        
        # Ensure directories exist
        self.health_data_dir.mkdir(parents=True, exist_ok=True)
        self.research_data_dir.mkdir(parents=True, exist_ok=True)
        self.tools_data_dir.mkdir(parents=True, exist_ok=True)

    async def initialize_test_data(self, test_data: Dict[str, Any]) -> None:
        """Initialize test data for all servers."""
        try:
            # Save health data
            if DataCategory.HEALTH_METRICS.value in test_data:
                health_data = test_data[DataCategory.HEALTH_METRICS.value]
                
                # Save health data to CSV
                health_data_path = self.health_data_dir / "test_health_data.csv"
                health_data_dict = {
                    "active_calories": health_data["active_calories"],
                    "steps": health_data.get("steps", 0),
                    "heart_rate": health_data.get("heart_rate", 0),
                    "sleep_hours": health_data.get("sleep_hours", 0)
                }
                df = pd.DataFrame([health_data_dict])
                df.to_csv(health_data_path, index=False)
                
                # Save daily metrics to JSON
                daily_metrics_path = self.health_data_dir / "daily_metrics.json"
                with open(daily_metrics_path, 'w') as f:
                    json.dump(health_data.get("daily_metrics", {}), f, indent=2)
                
                # Save user data
                user_data_path = self.health_data_dir / "test_user.json"
                user_data = {
                    "health_data": health_data_dict,
                    "daily_metrics": health_data.get("daily_metrics", [])
                }
                with open(user_data_path, 'w') as f:
                    json.dump(user_data, f, indent=2)
                    
            # Save research data
            if DataCategory.BIOMARKERS.value in test_data:
                papers_path = self.research_data_dir / "test_papers.json"
                biomarkers = test_data[DataCategory.BIOMARKERS.value]
                
                # Format papers for research server
                papers = []
                for biomarker_id, value in biomarkers.items():
                    papers.append({
                        "title": f"Research on {biomarker_id}",
                        "keywords": ["biomarkers", biomarker_id],
                        "abstract": f"Research paper discussing {biomarker_id} with value {value}",
                        "publication_date": datetime.now().strftime("%Y-%m-%d"),
                        "doi": f"10.1234/test.{biomarker_id}"
                    })
                
                # Save papers with biomarkers key
                research_data = {
                    "biomarkers": biomarkers,
                    "papers": papers
                }
                with open(papers_path, 'w') as f:
                    json.dump(research_data, f, indent=2)
                    
            # Save tools data
            if DataCategory.FITNESS_METRICS.value in test_data:
                tools_path = self.tools_data_dir / "test_tools_config.json"
                fitness_metrics = test_data[DataCategory.FITNESS_METRICS.value]
                tools_data = {
                    "biological_age": {
                        "metrics": fitness_metrics,
                        "thresholds": {
                            "push_ups": {"min": 10, "max": 30},
                            "grip_strength": {"min": 80, "max": 130},
                            "vo2_max": {"min": 30, "max": 50}
                        }
                    },
                    "fitness_metrics": fitness_metrics
                }
                with open(tools_path, 'w') as f:
                    json.dump(tools_data, f, indent=2)
                    
        except Exception as e:
            print(f"Error initializing test data: {str(e)}")
            raise

    async def load_server_data(self, server_type: str) -> Dict[str, Any]:
        """Load data for a specific server type."""
        try:
            if server_type == "health":
                # Load health data from CSV
                health_data_path = self.health_data_dir / "test_health_data.csv"
                if health_data_path.exists():
                    df = pd.read_csv(health_data_path)
                    health_data = df.iloc[0].to_dict()
                    # Convert any NaN values to None
                    health_data = {k: None if pd.isna(v) else v for k, v in health_data.items()}
                else:
                    health_data = {}
                
                # Load daily metrics from JSON
                daily_metrics_path = self.health_data_dir / "daily_metrics.json"
                if daily_metrics_path.exists():
                    with open(daily_metrics_path) as f:
                        daily_metrics = json.load(f)
                else:
                    daily_metrics = {}
                
                # Load user data from JSON
                user_data_path = self.health_data_dir / "test_user.json"
                if user_data_path.exists():
                    with open(user_data_path) as f:
                        user_data = json.load(f)
                        if "health_data" in user_data:
                            # Ensure we don't overwrite the CSV data
                            health_data.update(user_data["health_data"])
                
                # Return the combined data
                return {
                    "health_data": health_data,
                    "daily_metrics": daily_metrics
                }
                
            elif server_type == "research":
                # Load research papers
                papers_path = self.research_data_dir / "test_papers.json"
                if papers_path.exists():
                    with open(papers_path) as f:
                        return json.load(f)
                return {}
                
            elif server_type == "tools":
                # Load tools configuration
                tools_path = self.tools_data_dir / "test_tools_config.json"
                if tools_path.exists():
                    with open(tools_path) as f:
                        return json.load(f)
                return {}
                
            return {}
            
        except Exception as e:
            print(f"Error loading data for {server_type}: {str(e)}")
            return {}

    async def update_server_data(self, server_type: str, data: Dict[str, Any]) -> None:
        """Update data for a specific server type."""
        if server_type == "health":
            # Extract health data from the input
            health_data = data.get("health_data", {})
            
            # Update CSV file
            health_data_path = self.health_data_dir / "test_health_data.csv"
            df = pd.DataFrame([health_data])
            df.to_csv(health_data_path, index=False)
            
            # Update user data file
            user_data_path = self.health_data_dir / "test_user.json"
            user_data = {"health_data": health_data}
            with open(user_data_path, 'w') as f:
                json.dump(user_data, f, indent=2)
                
        elif server_type == "research":
            with open(self.research_data_dir / "test_papers.json", "w") as f:
                json.dump(data, f, indent=2)
        elif server_type == "tools":
            with open(self.tools_data_dir / "test_tools_config.json", "w") as f:
                json.dump(data, f, indent=2)

    @staticmethod
    async def initialize_servers(api_key: str, data_dir: str = "data") -> Dict[str, Any]:
        """Initialize all MCP servers with test data."""
        manager = MCPDataManager(data_dir)
        
        # Create server instances
        servers = {
            "health": HealthServer(api_key, str(manager.health_data_dir)),
            "research": ResearchServer(api_key, str(manager.research_data_dir)),
            "tools": ToolsServer(api_key, str(manager.tools_data_dir))
        }
        
        # Load initial data
        for server_type, server in servers.items():
            data = await manager.load_server_data(server_type)
            if data:
                if server_type == "health":
                    # Convert to the expected format for health server
                    health_metrics = {
                        "health_metrics": {
                            "active_calories": data["health_data"]["active_calories"],
                            "steps": data["health_data"].get("steps", 0),
                            "heart_rate": data["health_data"].get("heart_rate", 0),
                            "sleep_hours": data["health_data"].get("sleep_hours", 0),
                            "daily_metrics": data.get("daily_metrics", {})
                        }
                    }
                    await server.initialize_data(health_metrics)
                else:
                    await server.initialize_data(data)
        
        return servers 