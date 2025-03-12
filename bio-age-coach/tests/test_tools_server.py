"""
Tools server tests.
"""

import pytest
import os
from bio_age_coach.mcp.tools_server import ToolsServer

@pytest.fixture
async def tools_server():
    """Create a tools server instance with test data."""
    api_key = "test_api_key"
    data_path = "data/test/tools"
    
    # Ensure test directory exists
    os.makedirs(data_path, exist_ok=True)
    
    # Create server instance
    server = ToolsServer(api_key, data_path)
    return server

@pytest.mark.asyncio
async def test_get_config(tools_server):
    """Test getting server configuration."""
    request = {
        "api_key": "test_api_key",
        "type": "get_config"
    }
    
    response = await tools_server.handle_request(request)
    assert "error" not in response
    assert "config" in response
    assert "tools" in response["config"]
    assert "fitness_metrics" in response["config"]
    assert "tool_name" in response["config"]

@pytest.mark.asyncio
async def test_query(tools_server):
    """Test running a tool query."""
    request = {
        "api_key": "test_api_key",
        "type": "query",
        "tool_name": "biological_age",
        "data": {
            "age": 35,
            "sex": "male",
            "active_calories": 400,
            "steps": 8000,
            "heart_rate": 65,
            "sleep_hours": 7.5
        }
    }
    
    response = await tools_server.handle_request(request)
    assert "error" not in response
    assert "result" in response
    assert isinstance(response["result"], dict)

@pytest.mark.asyncio
async def test_invalid_request_type(tools_server):
    """Test handling of invalid request type."""
    request = {
        "api_key": "test_api_key",
        "type": "invalid_type"
    }
    
    response = await tools_server.handle_request(request)
    assert "error" in response
    assert "Unknown request type" in response["error"]

@pytest.mark.asyncio
async def test_authentication(tools_server):
    """Test request authentication."""
    request = {
        "api_key": "wrong_key",
        "type": "query",
        "tool_name": "biological_age"
    }
    
    response = await tools_server.handle_request(request)
    assert "error" in response
    assert "Authentication failed" in response["error"]

@pytest.mark.asyncio
async def test_invalid_tool(tools_server):
    """Test handling of invalid tool name."""
    request = {
        "api_key": "test_api_key",
        "type": "query",
        "tool_name": "invalid_tool"
    }
    
    response = await tools_server.handle_request(request)
    assert "error" in response
    assert "Unknown tool" in response["error"] 