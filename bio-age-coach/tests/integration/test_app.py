"""Integration tests for the app."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json
import os
import tempfile

from bio_age_coach.mcp.client import MultiServerMCPClient
from bio_age_coach.router.router_adapter import RouterAdapter
from bio_age_coach.chatbot.coach import BioAgeCoach

@pytest.fixture
def mock_mcp_client():
    """Create a mock MCP client."""
    client = AsyncMock(spec=MultiServerMCPClient)
    
    async def mock_send_request(server_name, endpoint, data=None):
        if server_name == "health" and endpoint == "metrics":
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
        else:
            return {
                "response": f"Response from {server_name} server",
                "insights": [f"Insight from {server_name} server"]
            }
    
    client.send_request.side_effect = mock_send_request
    return client

@pytest.fixture
def mock_router_adapter():
    """Create a mock router adapter."""
    adapter = AsyncMock(spec=RouterAdapter)
    
    async def mock_route_query(user_id, query, metadata=None):
        return {
            "response": f"Response to: {query}",
            "insights": ["Test insight 1", "Test insight 2"],
            "visualization": None,
            "error": None
        }
    
    adapter.route_query = AsyncMock(side_effect=mock_route_query)
    return adapter

@pytest.fixture
def app(mock_mcp_client, mock_router_adapter):
    """Create a BioAgeCoach instance with mocked dependencies."""
    # The order of arguments is important - router_adapter should be the first parameter
    app = BioAgeCoach(router_adapter=mock_router_adapter, mcp_client=mock_mcp_client)
    return app

class TestApp:
    """Test the app."""
    
    @pytest.mark.asyncio
    async def test_process_message(self, app, mock_router_adapter):
        """Test processing a message."""
        # Process message
        response = await app.process_message("Show me my health metrics")
        
        # Verify router was called
        mock_router_adapter.route_query.assert_called_once()
        call_args = mock_router_adapter.route_query.call_args[1]  # Use indexing to get kwargs
        assert call_args["user_id"] == app.user_id
        assert call_args["query"] == "Show me my health metrics"
        
        # Verify response
        assert "response" in response
        assert "insights" in response
    
    @pytest.mark.asyncio
    async def test_process_message_with_metadata(self, app, mock_router_adapter):
        """Test processing a message with metadata."""
        # Set metadata in app context
        app.context.update({"source": "web", "session_id": "123"})
        
        # Process message
        response = await app.process_message("Show me my health metrics")
        
        # Verify router was called
        mock_router_adapter.route_query.assert_called_once()
        call_args = mock_router_adapter.route_query.call_args[1]  # Use indexing to get kwargs
        assert call_args["user_id"] == app.user_id
        assert call_args["query"] == "Show me my health metrics"
        
        # Verify response
        assert "response" in response
        assert "insights" in response
    
    @pytest.mark.asyncio
    async def test_upload_data(self, app, mock_mcp_client):
        """Test uploading data."""
        # Create test data
        test_data = {
            "sleep_data": [
                {"date": "2023-01-01", "sleep_hours": 7.5}
            ]
        }
        
        # Set up mock response
        mock_mcp_client.upload_file = AsyncMock(return_value={
            "status": "success",
            "message": "Data uploaded successfully"
        })
        
        # Upload data
        response = await app.handle_data_upload("sleep", test_data)
        
        # Verify response
        assert "response" in response
        assert "insights" in response
    
    @pytest.mark.asyncio
    async def test_error_handling(self, app, mock_router_adapter):
        """Test error handling."""
        # Set up mock to raise exception
        async def mock_route_query_error(user_id, query, metadata=None):
            raise Exception("Test error")
        
        mock_router_adapter.route_query = AsyncMock(side_effect=mock_route_query_error)
        
        # Process message
        response = await app.process_message("Show me my health metrics")
        
        # Verify error response
        assert "error" in response
        assert isinstance(response["error"], str)
        assert "Test error" in response["error"] 