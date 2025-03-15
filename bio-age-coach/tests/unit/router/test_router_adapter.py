"""Tests for the router adapter."""

import pytest
import asyncio
from unittest.mock import MagicMock, patch
from typing import Dict, Any, List
from bio_age_coach.router.router_adapter import RouterAdapter
from bio_age_coach.router.semantic_router import SemanticRouter
from bio_age_coach.mcp.client import MultiServerMCPClient
from bio_age_coach.mcp.core.module_registry import ModuleRegistry

@pytest.fixture
def mock_semantic_router():
    """Create a mock semantic router."""
    router = MagicMock(spec=SemanticRouter)
    
    async def mock_route_query(user_id, query, metadata=None):
        return {
            "response": "Response from semantic router",
            "insights": ["Insight 1", "Insight 2"],
            "visualization": {"type": "line", "data": [1, 2, 3]},
            "error": None
        }
    
    router.route_query.side_effect = mock_route_query
    router.get_active_topic.return_value = "bio_age"
    
    return router

@pytest.fixture
def mock_mcp_client():
    """Create a mock MCP client."""
    client = MagicMock(spec=MultiServerMCPClient)
    
    async def mock_send_request(server_type, request):
        return {
            "response": f"Response from {server_type} server",
            "metrics": {"sleep": 7, "steps": 10000},
            "insights": [f"Insight from {server_type} server"]
        }
    
    client.send_request.side_effect = mock_send_request
    
    return client

@pytest.fixture
def mock_module_registry():
    """Create a mock module registry."""
    registry = MagicMock(spec=ModuleRegistry)
    registry.get_module_state.return_value = {"state": "active"}
    
    return registry

@pytest.fixture
def router_adapter(mock_semantic_router, mock_mcp_client, mock_module_registry):
    """Create a router adapter instance."""
    return RouterAdapter(
        semantic_router=mock_semantic_router,
        mcp_client=mock_mcp_client,
        module_registry=mock_module_registry
    )

@pytest.mark.asyncio
async def test_router_adapter_initialization(router_adapter, mock_semantic_router, mock_mcp_client, mock_module_registry):
    """Test router adapter initialization."""
    assert router_adapter.semantic_router == mock_semantic_router
    assert router_adapter.mcp_client == mock_mcp_client
    assert router_adapter.module_registry == mock_module_registry

@pytest.mark.asyncio
async def test_route_query(router_adapter, mock_semantic_router):
    """Test route_query method."""
    response = await router_adapter.route_query("user1", "What is my biological age?")
    
    # Verify semantic router was called
    mock_semantic_router.route_query.assert_called_once()
    call_args = mock_semantic_router.route_query.call_args
    assert call_args.kwargs["user_id"] == "user1"
    assert call_args.kwargs["query"] == "What is my biological age?"
    assert call_args.kwargs["metadata"] is None
    
    # Verify response format
    assert response["response"] == "Response from semantic router"
    assert response["insights"] == ["Insight 1", "Insight 2"]
    assert response["visualization"] == {"type": "line", "data": [1, 2, 3]}
    assert response["error"] is None

@pytest.mark.asyncio
async def test_route_query_with_metadata(router_adapter, mock_semantic_router):
    """Test route_query method with metadata."""
    metadata = {"key": "value"}
    response = await router_adapter.route_query("user1", "What is my biological age?", metadata)
    
    # Verify semantic router was called with metadata
    mock_semantic_router.route_query.assert_called_once()
    call_args = mock_semantic_router.route_query.call_args
    assert call_args.kwargs["user_id"] == "user1"
    assert call_args.kwargs["query"] == "What is my biological age?"
    assert call_args.kwargs["metadata"] == metadata

@pytest.mark.asyncio
async def test_route_query_health_analysis(router_adapter, mock_semantic_router):
    """Test route_query method for health analysis."""
    # Mock semantic router to return response without metrics
    async def mock_route_query(user_id, query, metadata=None):
        return {
            "response": "Response from semantic router",
            "insights": ["Insight 1", "Insight 2"],
            "visualization": None,
            "error": None
        }
    
    mock_semantic_router.route_query.side_effect = mock_route_query
    
    response = await router_adapter.route_query("user1", "Show me my health metrics")
    
    # Verify response has metrics field
    assert "metrics" in response
    assert response["metrics"] == {}

@pytest.mark.asyncio
async def test_route_query_bio_age(router_adapter, mock_semantic_router):
    """Test route_query method for bio age."""
    # Mock semantic router to return response without total_score
    async def mock_route_query(user_id, query, metadata=None):
        return {
            "response": "Response from semantic router",
            "insights": ["Insight 1", "Insight 2"],
            "visualization": None,
            "error": None
        }
    
    mock_semantic_router.route_query.side_effect = mock_route_query
    
    response = await router_adapter.route_query("user1", "What is my bio age score?")
    
    # Verify response has total_score field
    assert "total_score" in response
    assert response["total_score"] == 0

@pytest.mark.asyncio
async def test_get_active_topic(router_adapter, mock_semantic_router):
    """Test get_active_topic method."""
    topic = router_adapter.get_active_topic("user1")
    
    # Verify semantic router was called
    mock_semantic_router.get_active_topic.assert_called_once_with("user1")
    
    # Verify result
    assert topic == "bio_age"

@pytest.mark.asyncio
async def test_clear_context(router_adapter, mock_semantic_router):
    """Test clear_context method."""
    router_adapter.clear_context("user1")
    
    # Verify semantic router was called
    mock_semantic_router.clear_context.assert_called_once_with("user1") 