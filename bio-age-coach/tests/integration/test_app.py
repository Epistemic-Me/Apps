"""Integration tests for the Bio-Age Coach app."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from bio_age_coach.app import init_mcp_servers, load_user_data, get_daily_health_summary
from bio_age_coach.mcp.utils.client import MultiServerMCPClient
from bio_age_coach.mcp.core.router import QueryRouter
from bio_age_coach.chatbot.coach import BioAgeCoach

@pytest.fixture
def mock_mcp_client():
    """Create a mock MCP client."""
    client = Mock(spec=MultiServerMCPClient)
    client.send_request = AsyncMock(return_value={
        "metrics": [
            {
                "active_calories": 500,
                "steps": 10000,
                "sleep_hours": 8,
                "health_score": 85
            }
        ],
        "workouts": []
    })
    return client

@pytest.fixture
def mock_query_router():
    """Create a mock query router."""
    router = Mock(spec=QueryRouter)
    router.route_query = AsyncMock(return_value={
        "response": "Test response",
        "insights": ["Test insight"],
        "visualization": None,
        "error": None
    })
    return router

@pytest.fixture
def mock_coach():
    """Create a mock coach."""
    coach = Mock(spec=BioAgeCoach)
    coach.process_message = AsyncMock(return_value={
        "response": "Test response",
        "insights": ["Test insight"],
        "visualization": None,
        "error": None
    })
    return coach

@pytest.mark.asyncio
async def test_init_mcp_servers(mock_mcp_client):
    """Test initialization of MCP servers."""
    with patch('bio_age_coach.app.MultiServerMCPClient', return_value=mock_mcp_client):
        mcp_client, query_router = await init_mcp_servers()
        assert isinstance(mcp_client, MultiServerMCPClient)
        assert isinstance(query_router, QueryRouter)

@pytest.mark.asyncio
async def test_load_user_data(mock_mcp_client):
    """Test loading user data."""
    with patch('bio_age_coach.app.MultiServerMCPClient', return_value=mock_mcp_client):
        success = await load_user_data("test_user_1", mock_mcp_client)
        assert success is True
        mock_mcp_client.send_request.assert_called()

@pytest.mark.asyncio
async def test_get_daily_health_summary(mock_mcp_client):
    """Test getting daily health summary."""
    with patch('bio_age_coach.app.MultiServerMCPClient', return_value=mock_mcp_client):
        summary = await get_daily_health_summary("test_user_1", mock_mcp_client)
        assert summary is not None
        assert summary["avg_calories"] == 500
        assert summary["avg_steps"] == 10000
        assert summary["avg_sleep"] == 8
        assert summary["avg_score"] == 85

@pytest.mark.asyncio
async def test_app_error_handling(mock_mcp_client):
    """Test error handling in app functions."""
    # Test load_user_data error handling
    mock_mcp_client.send_request.side_effect = Exception("Test error")
    success = await load_user_data("test_user_1", mock_mcp_client)
    assert success is False

    # Test get_daily_health_summary error handling
    summary = await get_daily_health_summary("test_user_1", mock_mcp_client)
    assert summary is None

@pytest.mark.asyncio
async def test_app_data_flow(mock_mcp_client, mock_query_router, mock_coach):
    """Test data flow through the app."""
    # Initialize app components
    with patch('bio_age_coach.app.MultiServerMCPClient', return_value=mock_mcp_client), \
         patch('bio_age_coach.app.QueryRouter', return_value=mock_query_router), \
         patch('bio_age_coach.app.BioAgeCoach.create', return_value=mock_coach):
        
        # Test data flow
        mcp_client, query_router = await init_mcp_servers()
        success = await load_user_data("test_user_1", mcp_client)
        assert success is True
        
        summary = await get_daily_health_summary("test_user_1", mcp_client)
        assert summary is not None
        
        response = await mock_coach.process_message("test message")
        assert response["response"] == "Test response"
        assert response["insights"] == ["Test insight"] 