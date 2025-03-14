"""Test cases for MCP router."""

import pytest
from bio_age_coach.mcp.servers.health_server import HealthServer
from bio_age_coach.mcp.servers.bio_age_score_server import BioAgeScoreServer
from bio_age_coach.mcp.servers.research_server import ResearchServer
from bio_age_coach.mcp.servers.tools_server import ToolsServer

@pytest.fixture
def health_server():
    """Create a test health server."""
    return HealthServer("test_api_key")

@pytest.fixture
def bio_age_score_server():
    """Create a test bio age score server."""
    return BioAgeScoreServer("test_api_key")

@pytest.fixture
def research_server():
    """Create a test research server."""
    return ResearchServer("test_api_key")

@pytest.fixture
def tools_server():
    """Create a test tools server."""
    return ToolsServer("test_api_key")

@pytest.mark.asyncio
async def test_health_query_routing(health_server):
    """Test routing of health queries."""
    request = {
        "type": "metrics",
        "timeframe": "1D",
        "api_key": "test_api_key"
    }
    response = await health_server.handle_request(request)
    assert "error" not in response
    assert "metrics" in response
    assert isinstance(response["metrics"], list)

@pytest.mark.asyncio
async def test_research_query_routing(research_server):
    """Test routing of research queries."""
    request = {
        "type": "get_insights",
        "query": "sleep and aging",
        "api_key": "test_api_key"
    }
    response = await research_server.handle_request(request)
    assert "error" not in response
    assert "insights" in response

@pytest.mark.asyncio
async def test_tools_query_routing(tools_server):
    """Test routing of tools queries."""
    request = {
        "type": "biological_age",
        "metrics": {
            "sleep_hours": 7.5,
            "active_calories": 400,
            "steps": 8000
        },
        "api_key": "test_api_key"
    }
    response = await tools_server.handle_request(request)
    assert "error" not in response
    assert "biological_age" in response 