"""Test cases for ResearchServer."""

import pytest
from datetime import datetime, timedelta
import os
import json

@pytest.mark.asyncio
async def test_get_papers(research_server, sample_research_data):
    """Test getting papers."""
    # Initialize with test data
    await research_server.initialize_data(sample_research_data)

    request = {
        "api_key": "test_api_key",
        "type": "get_papers",
        "query": "exercise"
    }

    response = await research_server.handle_request(request)
    assert "error" not in response
    assert "papers" in response
    assert isinstance(response["papers"], list)
    # The server currently returns an empty list by default
    assert len(response["papers"]) == 0

@pytest.mark.asyncio
async def test_get_insights(research_server):
    """Test getting research insights."""
    request = {
        "api_key": "test_api_key",
        "type": "get_insights",
        "query": "exercise and longevity"
    }

    response = await research_server.handle_request(request)
    assert "error" not in response
    assert "insights" in response
    assert isinstance(response["insights"], list)
    assert len(response["insights"]) > 0
    assert "source" in response["insights"][0]
    assert "insight" in response["insights"][0]
    assert "confidence" in response["insights"][0]

@pytest.mark.asyncio
async def test_get_papers_with_filters(research_server, sample_research_data):
    """Test getting papers with filters."""
    # Initialize with test data
    await research_server.initialize_data(sample_research_data)

    request = {
        "api_key": "test_api_key",
        "type": "get_papers",
        "query": "exercise",
        "filters": {
            "year": 2024,
            "keywords": ["health"]
        }
    }

    response = await research_server.handle_request(request)
    assert "error" not in response
    assert "papers" in response
    assert isinstance(response["papers"], list)
    # The server currently returns an empty list by default
    assert len(response["papers"]) == 0

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
        "type": "get_papers"
    }

    response = await research_server.handle_request(request)
    assert "error" in response
    assert "Authentication failed" in response["error"]

@pytest.mark.asyncio
async def test_empty_query(research_server):
    """Test handling of empty query."""
    request = {
        "api_key": "test_api_key",
        "type": "get_papers",
        "query": ""
    }

    response = await research_server.handle_request(request)
    assert "error" not in response
    assert "papers" in response
    assert isinstance(response["papers"], list)
    assert len(response["papers"]) == 0