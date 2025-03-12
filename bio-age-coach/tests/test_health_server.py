"""
Health server tests.
"""

import pytest
import os
from bio_age_coach.mcp.health_server import HealthServer
from bio_age_coach.mcp.data_manager import MCPDataManager
from bio_age_coach.types import DataCategory

@pytest.fixture
async def health_server():
    """Create a health server instance with test data."""
    api_key = "test_api_key"
    data_path = "data/test/health"
    
    # Ensure test directory exists
    os.makedirs(data_path, exist_ok=True)
    
    # Create server instance
    server = HealthServer(api_key, data_path)
    
    # Initialize with test data
    test_data = {
        DataCategory.HEALTH_METRICS.value: {
            "active_calories": 400,
            "steps": 8000,
            "heart_rate": 65,
            "sleep_hours": 7.5,
            "demographics": {
                "age": 35,
                "sex": "male"
            }
        }
    }
    
    await server.initialize_data(test_data)
    return server

@pytest.mark.asyncio
async def test_user_data_request(health_server):
    """Test getting user data."""
    request = {
        "api_key": "test_api_key",
        "type": "user_data",
        "user_id": "test_user"
    }
    
    response = await health_server.handle_request(request)
    assert "error" not in response
    assert "health_data" in response
    
    health_data = response["health_data"]
    assert health_data["active_calories"] == 400
    assert health_data["steps"] == 8000
    assert health_data["heart_rate"] == 65
    assert health_data["sleep_hours"] == 7.5

@pytest.mark.asyncio
async def test_update_request(health_server):
    """Test updating user data."""
    new_data = {
        "active_calories": 500,
        "steps": 10000,
        "heart_rate": 62,
        "sleep_hours": 8
    }
    
    request = {
        "api_key": "test_api_key",
        "type": "update",
        "user_id": "test_user",
        "data": new_data
    }
    
    response = await health_server.handle_request(request)
    assert "error" not in response
    assert response["status"] == "success"
    
    # Verify the update
    get_request = {
        "api_key": "test_api_key",
        "type": "user_data",
        "user_id": "test_user"
    }
    
    response = await health_server.handle_request(get_request)
    health_data = response["health_data"]
    assert health_data["active_calories"] == 500
    assert health_data["steps"] == 10000
    assert health_data["heart_rate"] == 62
    assert health_data["sleep_hours"] == 8

@pytest.mark.asyncio
async def test_users_request(health_server):
    """Test listing users."""
    request = {
        "api_key": "test_api_key",
        "type": "users"
    }
    
    response = await health_server.handle_request(request)
    assert "error" not in response
    assert "users" in response
    assert isinstance(response["users"], list)

@pytest.mark.asyncio
async def test_trends_request(health_server):
    """Test getting health trends."""
    request = {
        "api_key": "test_api_key",
        "type": "trends",
        "user_id": "test_user"
    }
    
    response = await health_server.handle_request(request)
    assert "error" not in response
    assert "trends" in response
    assert "steps" in response["trends"]
    assert response["trends"]["steps"]["current"] == 8000
    assert response["trends"]["steps"]["trend"] == "stable"

@pytest.mark.asyncio
async def test_invalid_request_type(health_server):
    """Test handling of invalid request type."""
    request = {
        "api_key": "test_api_key",
        "type": "invalid_type"
    }
    
    response = await health_server.handle_request(request)
    assert "error" in response
    assert "Unknown request type" in response["error"]

@pytest.mark.asyncio
async def test_authentication(health_server):
    """Test request authentication."""
    request = {
        "api_key": "wrong_key",
        "type": "user_data",
        "user_id": "test_user"
    }
    
    response = await health_server.handle_request(request)
    assert "error" in response
    assert "Authentication failed" in response["error"] 