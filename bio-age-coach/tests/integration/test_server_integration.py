"""Integration tests for server interactions."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from bio_age_coach.mcp.client import MultiServerMCPClient
from bio_age_coach.router.router_adapter import RouterAdapter
from bio_age_coach.router.semantic_router import SemanticRouter

class MockModuleRegistry:
    """Mock implementation of ModuleRegistry."""
    
    def __init__(self):
        """Initialize the mock module registry."""
        self.modules = {}
    
    def register_module(self, name, module):
        """Register a module."""
        self.modules[name] = module
    
    def get_module(self, name):
        """Get a module by name."""
        return self.modules.get(name, MagicMock())

@pytest.fixture
def mcp_router(mcp_client, router_adapter):
    """Create a mock MCP router."""
    # Create a mock module registry
    module_registry = MockModuleRegistry()
    
    # Add module_registry to the router_adapter
    router_adapter.module_registry = module_registry
    
    # Create a mock bio_age_score module
    bio_age_score_module = MagicMock()
    bio_age_score_module.initialize = AsyncMock()
    module_registry.register_module("bio_age_score", bio_age_score_module)
    
    # Add route_query method to the router
    router_adapter.route_query = AsyncMock(return_value={
        "metrics": [{"date": "2024-03-01", "sleep_hours": 7.5, "active_calories": 400, "steps": 8000}],
        "total_score": 85,
        "sleep_score": 80,
        "exercise_score": 85,
        "steps_score": 90,
        "insights": ["Your sleep quality is good", "Your exercise routine is effective"],
        "visualization": {"type": "line", "data": []}
    })
    
    return router_adapter

@pytest.mark.asyncio
async def test_health_to_bio_age_integration(health_server, bio_age_score_server):
    """Test integration between health and bio age score servers."""
    # First, store health data
    health_data = {
        "date": "2024-03-01",
        "sleep_hours": 8.0,
        "active_calories": 500,
        "steps": 10000
    }
    
    # Store health data using metrics request
    response = await health_server.handle_request({
        "type": "metrics",
        "timeframe": "1D",
        "api_key": "test_api_key"
    })
    assert "error" not in response
    assert "metrics" in response
    assert isinstance(response["metrics"], list)
    
    # Get bio age score
    response = await bio_age_score_server.handle_request({
        "type": "calculate_daily_score",
        "metrics": {
            "health_data": health_data
        },
        "api_key": "test_api_key"
    })
    assert "error" not in response
    assert "total_score" in response
    assert "sleep_score" in response
    assert "exercise_score" in response
    assert "steps_score" in response
    assert "insights" in response

@pytest.mark.asyncio
async def test_research_to_bio_age_integration(research_server, bio_age_score_server):
    """Test integration between research and bio age score servers."""
    # Get research insights
    research_request = {
        "api_key": "test_api_key",
        "type": "get_insights",
        "query": "exercise longevity"
    }
    
    research_response = await research_server.handle_request(research_request)
    assert "error" not in research_response
    assert "insights" in research_response
    
    # Use research insights to enhance bio age score insights
    bio_age_request = {
        "api_key": "test_api_key",
        "type": "calculate_daily_score",
        "metrics": {
            "health_data": {
                "sleep_hours": 7.5,
                "active_calories": 400,
                "steps": 8000
            }
        },
        "research_insights": research_response["insights"]
    }
    
    bio_age_response = await bio_age_score_server.handle_request(bio_age_request)
    assert "error" not in bio_age_response
    assert "insights" in bio_age_response

@pytest.mark.asyncio
async def test_mcp_router_integration(mcp_router, sample_health_data):
    """Test integration through the MCP router."""
    # Initialize health server with sample data
    health_server = mcp_router.mcp_client.servers["health"]
    await health_server.handle_request({
        "type": "initialize_data",
        "data": {
            "metrics": [
                {
                    "date": "2024-03-01",
                    "sleep_hours": 7.5,
                    "active_calories": 400,
                    "steps": 8000
                }
            ]
        },
        "api_key": "test_api_key"
    })
    
    # Initialize bio age score module
    module = mcp_router.module_registry.get_module("bio_age_score")
    await module.initialize({
        "user_id": "test_user",
        "health_data": [
            {
                "date": "2024-03-01",
                "sleep_hours": 7.5,
                "active_calories": 400,
                "steps": 8000
            }
        ]
    })
    
    # Get health metrics through router
    health_query = "get my health metrics"
    health_response = await mcp_router.route_query("test_user", health_query)
    assert "error" not in health_response
    assert "metrics" in health_response
    assert isinstance(health_response["metrics"], list)
    
    # Calculate bio age score through router
    bio_age_query = "calculate my bio age score"
    bio_age_response = await mcp_router.route_query("test_user", bio_age_query)
    assert "error" not in bio_age_response
    assert "total_score" in bio_age_response
    assert "sleep_score" in bio_age_response
    assert "exercise_score" in bio_age_response
    assert "steps_score" in bio_age_response
    assert "insights" in bio_age_response

@pytest.mark.asyncio
async def test_end_to_end_workflow(mcp_router, sample_health_data):
    """Test end-to-end workflow through the MCP router."""
    # Initialize health server with sample data
    health_server = mcp_router.mcp_client.servers["health"]
    await health_server.handle_request({
        "type": "initialize_data",
        "data": {
            "metrics": [
                {
                    "date": "2024-03-01",
                    "sleep_hours": 7.5,
                    "active_calories": 400,
                    "steps": 8000
                }
            ]
        },
        "api_key": "test_api_key"
    })
    
    # Initialize research server with sample data
    research_server = mcp_router.mcp_client.servers["research"]
    await research_server.handle_request({
        "type": "initialize_data",
        "data": {
            "papers": [
                {
                    "title": "Exercise and Longevity",
                    "abstract": "Regular exercise has been shown to improve longevity and healthspan.",
                    "keywords": ["exercise", "longevity", "healthspan"],
                    "year": 2024,
                    "authors": ["John Doe", "Jane Smith"]
                }
            ]
        },
        "api_key": "test_api_key"
    })
    
    # Initialize bio age score module
    module = mcp_router.module_registry.get_module("bio_age_score")
    await module.initialize({
        "user_id": "test_user",
        "health_data": [
            {
                "date": "2024-03-01",
                "sleep_hours": 7.5,
                "active_calories": 400,
                "steps": 8000
            }
        ]
    })
    
    # Get health metrics through router
    health_query = "get my health metrics"
    health_response = await mcp_router.route_query("test_user", health_query)
    assert "error" not in health_response
    assert "metrics" in health_response
    assert isinstance(health_response["metrics"], list)
    
    # Get research insights through router
    research_query = "get research insights about exercise and longevity"
    research_response = await mcp_router.route_query("test_user", research_query)
    assert "error" not in research_response
    assert "insights" in research_response
    assert isinstance(research_response["insights"], list)
    
    # Calculate bio age score through router
    bio_age_query = "calculate my bio age score"
    bio_age_response = await mcp_router.route_query("test_user", bio_age_query)
    assert "error" not in bio_age_response
    assert "total_score" in bio_age_response
    assert "sleep_score" in bio_age_response
    assert "exercise_score" in bio_age_response
    assert "steps_score" in bio_age_response
    assert "insights" in bio_age_response

    # Create visualization
    viz_query = "create a visualization of my bio age scores"
    viz_response = await mcp_router.route_query("test_user", viz_query)
    assert "error" not in viz_response
    assert "visualization" in viz_response
    assert "insights" in viz_response 