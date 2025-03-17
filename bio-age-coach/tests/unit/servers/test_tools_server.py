"""Test cases for ToolsServer."""

import pytest
from datetime import datetime, timedelta
import os
import json

@pytest.mark.asyncio
async def test_get_config(tools_server):
    """Test getting server configuration."""
    request = {
        "api_key": "test_api_key",
        "type": "get_config"
    }

    response = await tools_server.handle_request(request)
    assert "error" not in response
    assert "tools" in response
    assert "fitness_metrics" in response
    assert "tool_name" in response

@pytest.mark.asyncio
async def test_query_biological_age(tools_server, sample_health_data):
    """Test querying biological age calculation."""
    request = {
        "api_key": "test_api_key",
        "type": "query",
        "tool_name": "biological_age",
        "data": {
            "metrics": sample_health_data
        }
    }

    response = await tools_server.handle_request(request)
    assert "error" not in response
    assert "biological_age" in response
    assert "factors" in response

@pytest.mark.asyncio
async def test_query_health_score(tools_server, sample_health_data):
    """Test querying health score calculation."""
    request = {
        "api_key": "test_api_key",
        "type": "query",
        "tool_name": "health_score",
        "data": {
            "metrics": sample_health_data
        }
    }

    response = await tools_server.handle_request(request)
    assert "error" not in response
    assert "tool_name" in response
    assert "health_score" in response
    assert "components" in response

@pytest.mark.asyncio
async def test_query_fitness_metrics(tools_server, sample_health_data):
    """Test querying fitness metrics."""
    request = {
        "api_key": "test_api_key",
        "type": "query",
        "tool_name": "fitness_metrics"
    }

    response = await tools_server.handle_request(request)
    assert "error" not in response
    assert "tool_name" in response
    assert "metrics" in response

@pytest.mark.asyncio
async def test_query_analyze(tools_server):
    """Test querying data analysis."""
    data_series = [
        {
            "date": (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d"),
            "sleep_hours": 7.5 - (i * 0.1),
            "active_calories": 400 + (i * 10),
            "steps": 8000 + (i * 100)
        }
        for i in range(30)
    ]

    request = {
        "api_key": "test_api_key",
        "type": "query",
        "tool_name": "analyze",
        "data": {
            "data_series": data_series
        }
    }

    response = await tools_server.handle_request(request)
    assert "error" not in response
    assert "tool_name" in response
    assert "analysis" in response

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
        "type": "get_config"
    }

    response = await tools_server.handle_request(request)
    assert "error" in response
    assert "Authentication failed" in response["error"]

@pytest.mark.asyncio
async def test_invalid_tool_name(tools_server):
    """Test handling of invalid tool name."""
    request = {
        "api_key": "test_api_key",
        "type": "query",
        "tool_name": "invalid_tool"
    }

    response = await tools_server.handle_request(request)
    assert "error" in response
    assert "Unknown tool" in response["error"] 