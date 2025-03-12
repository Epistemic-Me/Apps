"""
Research server tests.
"""

import pytest
import os
from bio_age_coach.mcp.research_server import ResearchServer
from bio_age_coach.types import DataCategory

@pytest.fixture
async def research_server():
    """Create a research server instance with test data."""
    api_key = "test_api_key"
    data_path = "data/test/research"
    
    # Ensure test directory exists
    os.makedirs(data_path, exist_ok=True)
    
    # Create server instance
    server = ResearchServer(api_key, data_path)
    
    # Initialize with test data
    test_data = {
        "papers": [
            {
                "id": "paper1",
                "title": "Exercise and Longevity",
                "abstract": "Study on the effects of exercise on longevity.",
                "keywords": ["exercise", "longevity", "health"],
                "year": 2023,
                "authors": ["Smith, J.", "Jones, K."]
            },
            {
                "id": "paper2",
                "title": "Sleep Quality and Aging",
                "abstract": "Research on sleep quality impact on biological aging.",
                "keywords": ["sleep", "aging", "health"],
                "year": 2023,
                "authors": ["Brown, M.", "Wilson, R."]
            }
        ]
    }
    
    await server.initialize_data(test_data)
    return server

@pytest.mark.asyncio
async def test_get_insights(research_server):
    """Test getting research insights."""
    request = {
        "api_key": "test_api_key",
        "type": "get_insights",
        "query": "exercise longevity"
    }
    
    response = await research_server.handle_request(request)
    assert "error" not in response
    assert "insights" in response
    
    insights = response["insights"]
    assert isinstance(insights, list)
    assert len(insights) > 0
    
    # Check insight structure
    insight = insights[0]
    assert "source" in insight
    assert "insight" in insight
    assert "confidence" in insight

@pytest.mark.asyncio
async def test_get_papers(research_server):
    """Test getting papers."""
    request = {
        "api_key": "test_api_key",
        "type": "get_papers",
        "query": "exercise"
    }
    
    response = await research_server.handle_request(request)
    assert "error" not in response
    assert "papers" in response
    
    papers = response["papers"]
    assert isinstance(papers, list)

@pytest.mark.asyncio
async def test_invalid_request_type(research_server):
    """Test handling of invalid request type."""
    request = {
        "api_key": "test_api_key",
        "type": "invalid_type"
    }
    
    response = await research_server.handle_request(request)
    assert "error" in response
    assert "Unknown request type" in response["error"]

@pytest.mark.asyncio
async def test_authentication(research_server):
    """Test request authentication."""
    request = {
        "api_key": "wrong_key",
        "type": "get_insights",
        "query": "exercise"
    }
    
    response = await research_server.handle_request(request)
    assert "error" in response
    assert "Authentication failed" in response["error"]

@pytest.mark.asyncio
async def test_empty_query(research_server):
    """Test handling of empty query."""
    request = {
        "api_key": "test_api_key",
        "type": "get_insights",
        "query": ""
    }
    
    response = await research_server.handle_request(request)
    assert "error" not in response
    assert "insights" in response
    assert isinstance(response["insights"], list)

@pytest.mark.asyncio
async def test_paper_caching(research_server):
    """Test that paper results are cached."""
    # First request
    request = {
        "api_key": "test_api_key",
        "type": "get_papers",
        "query": "exercise"
    }
    
    response1 = await research_server.handle_request(request)
    papers1 = response1["papers"]
    
    # Second request with same query
    response2 = await research_server.handle_request(request)
    papers2 = response2["papers"]
    
    # Results should be the same
    assert papers1 == papers2 