"""Integration tests for the app with semantic router."""

import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
import os
import sys

# Add the app directory to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from bio_age_coach.mcp.utils.client import MultiServerMCPClient
from bio_age_coach.router.router_adapter import RouterAdapter
from bio_age_coach.router.semantic_router import SemanticRouter
from bio_age_coach.agents.factory import create_agents
from bio_age_coach.chatbot.coach import BioAgeCoach

@pytest.fixture
async def mock_mcp_client():
    """Create a mock MCP client."""
    client = AsyncMock(spec=MultiServerMCPClient)
    
    async def mock_send_request(server_type, request):
        if server_type == "health" and request.get("type") == "metrics":
            return {
                "metrics": [
                    {
                        "date": "2023-01-01",
                        "sleep_hours": 7.5,
                        "active_calories": 400,
                        "steps": 8000,
                        "heart_rate": 70,
                        "health_score": 85
                    }
                ],
                "workouts": []
            }
        elif server_type == "bio_age_score" and request.get("type") == "initialize":
            return {"status": "success"}
        else:
            return {
                "response": f"Response from {server_type} server",
                "insights": [f"Insight from {server_type} server"]
            }
    
    client.send_request.side_effect = mock_send_request
    
    return client

@pytest.fixture
async def mock_router_adapter(mock_mcp_client):
    """Create a mock router adapter."""
    adapter = AsyncMock(spec=RouterAdapter)
    
    async def mock_route_query(user_id, query, metadata=None):
        return {
            "response": f"Response to: {query}",
            "insights": ["Test insight 1", "Test insight 2"],
            "visualization": None,
            "error": None
        }
    
    async def mock_handle_data_upload(user_id, data_type, data):
        return {
            "response": f"Processed {data_type} data",
            "insights": ["Test insight 1", "Test insight 2"],
            "visualization": None,
            "error": None
        }
    
    adapter.route_query.side_effect = mock_route_query
    adapter.handle_data_upload.side_effect = mock_handle_data_upload
    
    return adapter

@pytest.fixture
async def mock_coach(mock_mcp_client, mock_router_adapter):
    """Create a mock coach."""
    coach = await BioAgeCoach.create(mock_mcp_client, mock_router_adapter)
    return coach

@pytest.mark.asyncio
async def test_init_mcp_servers():
    """Test initializing MCP servers with semantic router."""
    with patch('bio_age_coach.mcp.utils.client.MultiServerMCPClient') as mock_client_class:
        with patch('bio_age_coach.mcp.servers.health_server.HealthServer') as mock_health_server_class:
            with patch('bio_age_coach.mcp.servers.research_server.ResearchServer') as mock_research_server_class:
                with patch('bio_age_coach.mcp.servers.tools_server.ToolsServer') as mock_tools_server_class:
                    with patch('bio_age_coach.mcp.servers.bio_age_score_server.BioAgeScoreServer') as mock_bio_age_score_server_class:
                        with patch('bio_age_coach.agents.factory.create_agents') as mock_create_agents:
                            with patch('bio_age_coach.router.semantic_router.SemanticRouter') as mock_semantic_router_class:
                                with patch('bio_age_coach.router.router_adapter.RouterAdapter') as mock_router_adapter_class:
                                    # Setup mocks
                                    mock_client = AsyncMock()
                                    mock_client_class.return_value = mock_client
                                    
                                    mock_health_server = AsyncMock()
                                    mock_health_server_class.return_value = mock_health_server
                                    
                                    mock_research_server = AsyncMock()
                                    mock_research_server_class.return_value = mock_research_server
                                    
                                    mock_tools_server = AsyncMock()
                                    mock_tools_server_class.return_value = mock_tools_server
                                    
                                    mock_bio_age_score_server = AsyncMock()
                                    mock_bio_age_score_server_class.return_value = mock_bio_age_score_server
                                    
                                    mock_agents = [MagicMock(), MagicMock()]
                                    mock_create_agents.return_value = mock_agents
                                    
                                    mock_semantic_router = MagicMock()
                                    mock_semantic_router_class.return_value = mock_semantic_router
                                    
                                    mock_router_adapter = MagicMock()
                                    mock_router_adapter_class.return_value = mock_router_adapter
                                    
                                    # Mock client.send_request to return metrics data
                                    async def mock_send_request(server_type, request):
                                        return {
                                            "metrics": [
                                                {
                                                    "date": "2023-01-01",
                                                    "sleep_hours": 7.5,
                                                    "active_calories": 400,
                                                    "steps": 8000,
                                                    "heart_rate": 70
                                                }
                                            ]
                                        }
                                    
                                    mock_client.send_request.side_effect = mock_send_request
                                    
                                    # Import the function here to avoid circular imports
                                    from app import init_mcp_servers
                                    
                                    # Call the function
                                    mcp_client, router_adapter = await init_mcp_servers()
                                    
                                    # Verify the results
                                    assert mcp_client == mock_client
                                    assert router_adapter == mock_router_adapter
                                    
                                    # Verify the calls
                                    mock_client.add_server.assert_any_call("health", mock_health_server)
                                    mock_client.add_server.assert_any_call("research", mock_research_server)
                                    mock_client.add_server.assert_any_call("tools", mock_tools_server)
                                    mock_client.add_server.assert_any_call("bio_age_score", mock_bio_age_score_server)
                                    
                                    mock_create_agents.assert_called_once()
                                    mock_semantic_router_class.assert_called_once()
                                    # Adjust the assertion to match the actual call
                                    mock_router_adapter_class.assert_called_once()

@pytest.mark.asyncio
async def test_coach_process_message(mock_coach, mock_router_adapter):
    """Test processing a message with the coach."""
    # Process a message
    response = await mock_coach.process_message("What is my biological age?")
    
    # Verify the response
    assert response is not None
    assert "response" in response
    assert "insights" in response
    
    # Verify router_adapter was called
    mock_router_adapter.route_query.assert_called_once()

@pytest.mark.asyncio
async def test_coach_handle_data_upload(mock_coach, mock_router_adapter):
    """Test handling data upload with the coach."""
    # Handle data upload
    response = await mock_coach.handle_data_upload(
        data_type="sleep",
        data={"sleep_data": [{"date": "2023-01-01", "sleep_hours": 7.5}]}
    )
    
    # Verify the response
    assert response is not None
    assert "response" in response
    assert "insights" in response
    
    # Verify router_adapter was called
    mock_router_adapter.handle_data_upload.assert_called_once() 