"""Tests for the QueryRouter class."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from bio_age_coach.mcp.core.router import QueryRouter
from bio_age_coach.mcp.core.module_registry import ModuleRegistry
from bio_age_coach.mcp.utils.client import MultiServerMCPClient

@pytest.fixture
def mock_mcp_client():
    """Create a mock MCP client."""
    client = AsyncMock(spec=MultiServerMCPClient)
    return client

@pytest.fixture
def mock_module_registry():
    """Create a mock module registry."""
    registry = MagicMock(spec=ModuleRegistry)
    return registry

@pytest.fixture
def router(mock_mcp_client, mock_module_registry):
    """Create a QueryRouter instance with mocked dependencies."""
    return QueryRouter(mock_mcp_client, mock_module_registry)

class TestIntentIdentification:
    """Test the intent identification functionality."""
    
    def test_health_analysis_intent(self, router):
        """Test identification of health analysis intent."""
        queries = [
            "Show me my health metrics",
            "Analyze my health data",
            "What's my health profile",
            "Display my health information"
        ]
        for query in queries:
            intent = router._identify_intent(query)
            assert intent == "health_analysis", f"Failed to identify health analysis intent in: {query}"
    
    def test_bio_age_intent(self, router):
        """Test identification of bio age intent."""
        queries = [
            "What's my bio age score",
            "Calculate my biological age",
            "Show my bio age",
            "What's my score"
        ]
        for query in queries:
            intent = router._identify_intent(query)
            assert intent == "bio_age", f"Failed to identify bio age intent in: {query}"
    
    def test_research_intent(self, router):
        """Test identification of research intent."""
        queries = [
            "Show me research about health",
            "What does the evidence say",
            "Find studies about bio age",
            "Show me scientific findings"
        ]
        for query in queries:
            assert router._identify_intent(query) == "research"
    
    def test_visualization_intent(self, router):
        """Test identification of visualization intent."""
        queries = [
            "Show me a graph of my health",
            "Display my health trends",
            "Create a chart of my data",
            "Plot my metrics over time"
        ]
        for query in queries:
            assert router._identify_intent(query) == "visualization"
    
    def test_unknown_intent(self, router):
        """Test handling of unknown intents."""
        queries = [
            "Hello",
            "How are you",
            "What's the weather",
            "Tell me a joke"
        ]
        for query in queries:
            assert router._identify_intent(query) == "unknown"

class TestTimeframeExtraction:
    """Test the timeframe extraction functionality."""
    
    def test_days_timeframe(self, router):
        """Test extraction of days timeframe."""
        queries = [
            "Show my health for the last 7 days",
            "Analyze my data from the past 14 days",
            "What's my health like over 30 days"
        ]
        expected_days = [7, 14, 30]
        for query, days in zip(queries, expected_days):
            timeframe = router._extract_timeframe(query)
            assert timeframe == f"{days}D", f"Failed to extract {days} days from: {query}"
    
    def test_weeks_timeframe(self, router):
        """Test extraction of weeks timeframe."""
        queries = [
            "Show my health for the last 2 weeks",
            "Analyze my data from the past 4 weeks",
            "What's my health like over 8 weeks"
        ]
        expected_days = [14, 28, 56]  # 2*7, 4*7, 8*7
        for query, days in zip(queries, expected_days):
            timeframe = router._extract_timeframe(query)
            assert timeframe == f"{days}D", f"Failed to extract {days} days from: {query}"
    
    def test_months_timeframe(self, router):
        """Test extraction of months timeframe."""
        queries = [
            "Show my health for the last 1 month",
            "Analyze my data from the past 3 months",
            "What's my health like over 6 months"
        ]
        expected_days = [30, 90, 180]  # 1*30, 3*30, 6*30
        for query, days in zip(queries, expected_days):
            timeframe = router._extract_timeframe(query)
            assert timeframe == f"{days}D", f"Failed to extract {days} days from: {query}"
    
    def test_default_timeframe(self, router):
        """Test default timeframe when none specified."""
        queries = [
            "Show my health metrics",
            "What's my bio age",
            "Analyze my data"
        ]
        for query in queries:
            assert router._extract_timeframe(query) == "30D"

class TestQueryRouting:
    """Test the query routing functionality."""
    
    @pytest.mark.asyncio
    async def test_health_analysis_routing(self, router, mock_mcp_client):
        """Test routing of health analysis queries."""
        # Mock health server response
        mock_mcp_client.send_request.return_value = {
            "metrics": {
                "sleep_hours": 7.5,
                "active_calories": 500,
                "steps": 10000
            },
            "visualization": {"type": "line", "data": []}
        }
        
        response = await router.route_query("user1", "Show me my health metrics")
        
        assert "error" not in response
        assert "metrics" in response
        assert "visualization" in response
        assert "insights" in response
        
        # Verify correct server calls
        mock_mcp_client.send_request.assert_called()
        calls = mock_mcp_client.send_request.call_args_list
        assert any(call[0][0] == "health" for call in calls)
        assert any(call[0][0] == "bio_age_score" for call in calls)
    
    @pytest.mark.asyncio
    async def test_bio_age_routing(self, router, mock_mcp_client):
        """Test routing of bio age queries."""
        # Mock bio age server response
        mock_mcp_client.send_request.return_value = {
            "total_score": 85,
            "insights": ["Your bio age is younger than your chronological age!"]
        }
        
        response = await router.route_query("user1", "What's my bio age score")
        
        assert "error" not in response
        assert "metrics" in response
        assert "visualization" in response
        assert "insights" in response
    
    @pytest.mark.asyncio
    async def test_research_routing(self, router, mock_mcp_client):
        """Test routing of research queries."""
        # Mock research server response
        mock_mcp_client.send_request.return_value = {
            "insights": ["Research shows that regular exercise can improve biological age."]
        }
        
        response = await router.route_query("user1", "Show me research about health")
        
        assert "error" not in response
        assert "insights" in response
    
    @pytest.mark.asyncio
    async def test_visualization_routing(self, router, mock_mcp_client):
        """Test routing of visualization queries."""
        # Mock health and bio age server responses
        mock_mcp_client.send_request.side_effect = [
            {"metrics": {"sleep_hours": 7.5, "active_calories": 500}},
            {"visualization": {"type": "line", "data": []}}
        ]
        
        response = await router.route_query("user1", "Show me a graph of my health")
        
        assert "error" not in response
        assert "visualization" in response
        assert "insights" in response
    
    @pytest.mark.asyncio
    async def test_error_handling(self, router, mock_mcp_client):
        """Test error handling in routing."""
        # Mock server error
        mock_mcp_client.send_request.return_value = {"error": "Server error"}
        
        response = await router.route_query("user1", "Show me my health metrics")
        
        assert "error" in response
        assert isinstance(response["error"], str)
    
    @pytest.mark.asyncio
    async def test_unknown_intent_routing(self, router):
        """Test routing of queries with unknown intent."""
        response = await router.route_query("user1", "Hello there")
        
        assert "error" in response
        assert "rephrasing" in response["error"].lower()

class TestContextManagement:
    """Test the context management functionality."""
    
    def test_context_creation(self, router):
        """Test creation of new user context."""
        router._update_context("user1", "Show my health", {"source": "web"})
        
        assert "user1" in router.context
        assert len(router.context["user1"]["queries"]) == 1
        assert router.context["user1"]["metadata"] == {"source": "web"}
    
    def test_context_update(self, router):
        """Test updating existing user context."""
        router._update_context("user1", "First query", {})
        router._update_context("user1", "Second query", {"source": "web"})
        
        assert len(router.context["user1"]["queries"]) == 2
        assert router.context["user1"]["metadata"] == {"source": "web"}
    
    def test_context_limit(self, router):
        """Test context query limit."""
        for i in range(15):
            router._update_context("user1", f"Query {i}", {})
        
        assert len(router.context["user1"]["queries"]) == 10
        assert router.context["user1"]["queries"][0]["text"] == "Query 5"
    
    def test_context_clear(self, router):
        """Test clearing user context."""
        router._update_context("user1", "Test query", {})
        router.clear_context("user1")
        
        assert "user1" not in router.context 