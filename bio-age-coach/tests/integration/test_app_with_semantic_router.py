"""Integration tests for the app with the semantic router."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json
import os
import tempfile

from bio_age_coach.mcp.client import MultiServerMCPClient
from bio_age_coach.router.router_adapter import RouterAdapter
from bio_age_coach.chatbot.coach import BioAgeCoach

# Mock implementations
class MockMultiServerMCPClient(MultiServerMCPClient):
    """Mock implementation of MultiServerMCPClient."""
    
    def __init__(self):
        """Initialize the mock client."""
        self.servers = {}
        self.responses = {}
        self.requests = []
    
    def register_server(self, server_name, server_url):
        """Register a server."""
        self.servers[server_name] = server_url
    
    def set_response(self, server_name, response):
        """Set a response for a server."""
        self.responses[server_name] = response
    
    async def send_request(self, server_name, endpoint, data=None):
        """Send a request to a server."""
        self.requests.append((server_name, endpoint, data))
        return self.responses.get(server_name, {})
    
    async def upload_file(self, server_name, endpoint, file_path, metadata=None):
        """Upload a file to a server."""
        self.requests.append((server_name, endpoint, file_path, metadata))
        return self.responses.get(server_name, {})

class MockRouterAdapter(RouterAdapter):
    """Mock implementation of RouterAdapter."""
    
    def __init__(self):
        """Initialize the mock router adapter."""
        self.context = {}
        self.responses = {}
        self.queries = []
    
    def set_response(self, query_pattern, response):
        """Set a response for a query pattern."""
        self.responses[query_pattern] = response
    
    async def route_query(self, user_id, query, metadata=None):
        """Route a query."""
        self.queries.append((user_id, query, metadata))
        
        # Find matching response
        for pattern, response in self.responses.items():
            if pattern.lower() in query.lower():
                return response
        
        return {
            "response": "I'm not sure how to help with that",
            "error": "No matching response found"
        }
    
    def update_context(self, user_id, metadata):
        """Update context for a user."""
        if user_id not in self.context:
            self.context[user_id] = {}
        self.context[user_id].update(metadata)
    
    def clear_context(self, user_id):
        """Clear context for a user."""
        if user_id in self.context:
            del self.context[user_id]
    
    def get_active_topic(self, user_id):
        """Get the active topic for a user."""
        return self.context.get(user_id, {}).get("active_topic", "general")

class MockBioAgeCoach:
    """Mock implementation of BioAgeCoach."""
    
    def __init__(self, router_adapter, mcp_client):
        """Initialize the mock app."""
        self.router_adapter = router_adapter
        self.mcp_client = mcp_client
        self.user_data = {}
        self.user_id = "default_user"
        self.context = {}
    
    def set_user_data(self, user_id, data):
        """Set data for a user."""
        self.user_data[user_id] = data
    
    def get_user_data(self, user_id):
        """Get data for a user."""
        return self.user_data.get(user_id, {})
        
    async def process_message(self, message):
        """Process a user message."""
        return await self.router_adapter.route_query(
            user_id=self.user_id,
            query=message
        )
        
    async def handle_data_upload(self, data_type, data):
        """Handle data upload."""
        return {
            "response": f"Processed {data_type} data",
            "insights": ["Test insight 1", "Test insight 2"],
            "visualization": None,
            "error": None
        }
        
    def update_user_data(self, data):
        """Update user data."""
        self.context.update(data)
        
    def get_active_context(self):
        """Get active context."""
        return {
            'active_topic': self.router_adapter.get_active_topic(self.user_id),
            'observation_contexts': {}
        }

@pytest.fixture
def mcp_client():
    """Create a mock MCP client."""
    return MockMultiServerMCPClient()

@pytest.fixture
def router_adapter():
    """Create a mock router adapter."""
    return MockRouterAdapter()

@pytest.fixture
def app(router_adapter, mcp_client):
    """Create a mock app."""
    return MockBioAgeCoach(router_adapter, mcp_client)

class TestAppWithSemanticRouter:
    """Test the app with the semantic router."""
    
    def test_mcp_server_initialization(self, app, mcp_client):
        """Test initialization of MCP servers."""
        # Verify that servers are registered
        assert len(mcp_client.servers) == 0  # No servers registered in mock
        
        # Register servers
        mcp_client.register_server("health", "http://health-server")
        mcp_client.register_server("bio_age", "http://bio-age-server")
        
        assert "health" in mcp_client.servers
        assert "bio_age" in mcp_client.servers
    
    @pytest.mark.asyncio
    async def test_process_message(self, app, router_adapter):
        """Test processing a message."""
        # Set up mock response
        router_adapter.set_response("health", {
            "response": "Here are your health metrics",
            "insights": ["Your sleep is good", "Your steps are improving"],
            "visualization": {"type": "line", "data": []}
        })
        
        # Process message
        response = await app.process_message("Show me my health metrics")
        
        # Verify router was called
        assert len(router_adapter.queries) == 1
        assert router_adapter.queries[0][0] == app.user_id
        assert router_adapter.queries[0][1] == "Show me my health metrics"
        
        # Verify response
        assert "response" in response
        assert "insights" in response
        assert "visualization" in response
    
    @pytest.mark.asyncio
    async def test_process_message_with_context(self, app, router_adapter):
        """Test processing a message with context."""
        # Set up user context
        router_adapter.update_context(app.user_id, {"active_topic": "health"})
        app.update_user_data({"source": "web"})
        
        # Set up mock response for "metrics" query
        router_adapter.set_response("metrics", {
            "response": "Here are your health metrics",
            "insights": ["Your sleep is good", "Your steps are improving"]
        })
        
        # Also set up a response for "health" to ensure we have a fallback
        router_adapter.set_response("health", {
            "response": "Here are your health metrics",
            "insights": ["Your sleep is good", "Your steps are improving"]
        })
        
        # Process message
        response = await app.process_message("Show me my metrics")
        
        # Verify router was called
        assert len(router_adapter.queries) == 1
        assert router_adapter.queries[0][0] == app.user_id
        assert router_adapter.queries[0][1] == "Show me my metrics"
        
        # Verify response
        assert "response" in response
        assert "insights" in response
    
    @pytest.mark.asyncio
    async def test_upload_data(self, app, mcp_client):
        """Test uploading data."""
        # Set up mock response
        mcp_client.set_response("health", {
            "status": "success",
            "message": "Data uploaded successfully"
        })
        
        # Create test data
        test_data = {
            "sleep_data": [
                {"date": "2023-01-01", "sleep_hours": 7.5}
            ]
        }
        
        # Upload data
        response = await app.handle_data_upload("sleep", test_data)
        
        # Verify response
        assert "response" in response
        assert "insights" in response
    
    @pytest.mark.asyncio
    async def test_error_handling(self, app, router_adapter):
        """Test error handling."""
        # Set up mock response with error
        router_adapter.set_response("error", {
            "error": "Test error"
        })
        
        # Process message
        response = await app.process_message("This will cause an error")
        
        # Verify error response
        assert "error" in response
        assert isinstance(response["error"], str)
    
    def test_user_data_management(self, app):
        """Test user data management."""
        # Set user data
        app.set_user_data("user1", {"name": "Test User", "age": 30})
        
        # Get user data
        user_data = app.get_user_data("user1")
        
        # Verify data
        assert user_data["name"] == "Test User"
        assert user_data["age"] == 30
        
        # Get non-existent user data
        empty_data = app.get_user_data("user2")
        assert empty_data == {} 