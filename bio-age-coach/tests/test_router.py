"""Tests for the RouterAdapter class."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from bio_age_coach.router.router_adapter import RouterAdapter
from bio_age_coach.router.semantic_router import SemanticRouter
from bio_age_coach.mcp.client import MultiServerMCPClient

@pytest.fixture
def mock_mcp_client():
    """Create a mock MCP client."""
    client = AsyncMock(spec=MultiServerMCPClient)
    return client

@pytest.fixture
def mock_semantic_router():
    """Create a mock semantic router."""
    router = MagicMock(spec=SemanticRouter)
    
    async def mock_route_query(user_id, query, metadata=None):
        # Simulate different responses based on query content
        if "health" in query.lower():
            return {
                "response": "Here are your health metrics",
                "insights": ["Your sleep is good", "Your steps are improving"],
                "visualization": {"type": "line", "data": []}
            }
        elif "bio age" in query.lower() or "score" in query.lower():
            return {
                "response": "Your bio age score is 85",
                "insights": ["Your bio age is younger than your chronological age!"],
                "total_score": 85
            }
        elif "research" in query.lower():
            return {
                "response": "Here's what research says",
                "insights": ["Research shows that regular exercise can improve biological age."]
            }
        elif "graph" in query.lower() or "chart" in query.lower():
            return {
                "response": "Here's a visualization of your data",
                "visualization": {"type": "line", "data": []}
            }
        else:
            return {
                "response": "I'm not sure how to help with that",
                "error": "Please try rephrasing your question"
            }
    
    router.route_query.side_effect = mock_route_query
    router.get_active_topic.return_value = "bio_age"
    
    return router

@pytest.fixture
def router_adapter(mock_mcp_client, mock_semantic_router):
    """Create a RouterAdapter instance with mocked dependencies."""
    return RouterAdapter(mock_semantic_router, mock_mcp_client)

class TestQueryRouting:
    """Test the query routing functionality."""
    
    @pytest.mark.asyncio
    async def test_health_analysis_routing(self, router_adapter, mock_semantic_router):
        """Test routing of health analysis queries."""
        response = await router_adapter.route_query("user1", "Show me my health metrics")
        
        # The error field may be None, which is fine - we just want to ensure it's not a real error
        assert response["error"] is None
        assert "metrics" in response
        assert "visualization" in response
        assert "insights" in response
        
        # Verify correct router calls
        mock_semantic_router.route_query.assert_called_once()
        call_args = mock_semantic_router.route_query.call_args
        assert call_args.kwargs["user_id"] == "user1"
        assert call_args.kwargs["query"] == "Show me my health metrics"
    
    @pytest.mark.asyncio
    async def test_bio_age_routing(self, router_adapter, mock_semantic_router):
        """Test routing of bio age queries."""
        response = await router_adapter.route_query("user1", "What's my bio age score")
        
        # The error field may be None, which is fine - we just want to ensure it's not a real error
        assert response["error"] is None
        assert "total_score" in response
        assert "insights" in response
    
    @pytest.mark.asyncio
    async def test_research_routing(self, router_adapter, mock_semantic_router):
        """Test routing of research queries."""
        response = await router_adapter.route_query("user1", "Show me research about health")
        
        # The error field may be None, which is fine - we just want to ensure it's not a real error
        assert response["error"] is None
        assert "insights" in response
    
    @pytest.mark.asyncio
    async def test_visualization_routing(self, router_adapter, mock_semantic_router):
        """Test routing of visualization queries."""
        response = await router_adapter.route_query("user1", "Show me a graph of my health")
        
        # The error field may be None, which is fine - we just want to ensure it's not a real error
        assert response["error"] is None
        assert "visualization" in response
        assert "insights" in response
    
    @pytest.mark.asyncio
    async def test_error_handling(self, router_adapter, mock_semantic_router):
        """Test error handling in routing."""
        # Set up mock to return error
        async def mock_route_query_error(user_id, query, metadata=None):
            return {"error": "Server error"}
        
        mock_semantic_router.route_query.side_effect = mock_route_query_error
        
        response = await router_adapter.route_query("user1", "Show me my health metrics")
        
        assert "error" in response
        assert isinstance(response["error"], str)
    
    @pytest.mark.asyncio
    async def test_unknown_intent_routing(self, router_adapter):
        """Test routing of queries with unknown intent."""
        response = await router_adapter.route_query("user1", "Hello there")
        
        assert "error" in response
        assert "rephrasing" in response["error"].lower()

class TestContextManagement:
    """Test the context management functionality."""
    
    def test_context_creation(self, router_adapter):
        """Test creation of new user context."""
        router_adapter.update_context("user1", {"source": "web"})
        
        assert "user1" in router_adapter.context
        assert router_adapter.context["user1"] == {"source": "web"}
    
    def test_context_update(self, router_adapter):
        """Test updating existing user context."""
        router_adapter.update_context("user1", {"first": "value"})
        router_adapter.update_context("user1", {"second": "value"})
        
        assert "user1" in router_adapter.context
        assert router_adapter.context["user1"] == {"first": "value", "second": "value"}
    
    def test_context_clear(self, router_adapter, mock_semantic_router):
        """Test clearing user context."""
        router_adapter.update_context("user1", {"test": "value"})
        router_adapter.clear_context("user1")
        
        assert "user1" not in router_adapter.context
        mock_semantic_router.clear_context.assert_called_once_with("user1")
    
    def test_get_active_topic(self, router_adapter, mock_semantic_router):
        """Test getting active topic."""
        topic = router_adapter.get_active_topic("user1")
        
        assert topic == "bio_age"
        mock_semantic_router.get_active_topic.assert_called_once_with("user1") 