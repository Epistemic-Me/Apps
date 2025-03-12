"""Tests for the QueryRouter."""

import pytest
import os
import json
import logging
from bio_age_coach.mcp.router import QueryRouter
from bio_age_coach.mcp.health_server import HealthServer
from bio_age_coach.mcp.research_server import ResearchServer
from bio_age_coach.mcp.tools_server import ToolsServer

# Configure logging
logging.basicConfig(level=logging.INFO)

@pytest.fixture
def router(tmp_path):
    """Create a QueryRouter instance for testing."""
    # Create test data directories
    test_data_dir = tmp_path / "test_data"
    test_papers_dir = tmp_path / "test_papers"
    test_data_dir.mkdir(exist_ok=True)
    test_papers_dir.mkdir(exist_ok=True)
    
    logging.info(f"\nCreating test papers in {test_papers_dir}")
    
    # Create test papers
    test_papers = [
        {
            "title": "Longevity Research Overview",
            "keywords": ["longevity", "aging", "lifespan"],
            "abstract": "A comprehensive review of longevity research."
        },
        {
            "title": "Biological Age Assessment Methods",
            "keywords": ["biological age", "aging", "biomarkers"],
            "abstract": "Methods for assessing biological age using various biomarkers."
        },
        {
            "title": "Exercise and Health",
            "keywords": ["exercise", "health", "fitness"],
            "abstract": "The impact of exercise on health outcomes."
        }
    ]
    
    for i, paper in enumerate(test_papers):
        paper_path = test_papers_dir / f"paper_{i}.json"
        logging.info(f"Creating paper {i} at {paper_path}")
        with open(paper_path, "w") as f:
            json.dump(paper, f)
    
    logging.info("Creating servers")
    health_server = HealthServer("test_key", str(test_data_dir))
    research_server = ResearchServer("test_key", str(test_papers_dir))
    tools_server = ToolsServer("test_key")
    return QueryRouter(health_server, research_server, tools_server)

@pytest.mark.asyncio
async def test_health_query_routing(router):
    """Test routing of health-related queries."""
    # Test various health queries
    health_queries = [
        "show me my health data",
        "what are my activity metrics",
        "how many steps did I take",
        "show my apple health data",
        "what's my heart rate trend"
    ]
    
    for query in health_queries:
        result = await router.route_query(query)
        assert result["server"] == "health"
        
        # Check query type
        if "trend" in query:
            assert result["type"] == "trends"
        else:
            assert result["type"] == "metrics"

@pytest.mark.asyncio
async def test_research_query_routing(router):
    """Test routing of research-related queries."""
    # Test various research queries
    research_queries = [
        "find research papers about longevity",
        "show me studies on biological age",
        "what does the scientific literature say about exercise",
        "get paper details for this study"
    ]
    
    for query in research_queries:
        logging.info(f"\nTesting research query: {query}")
        result = await router.route_query(query)
        logging.info(f"Result: {result}")
        assert result["server"] == "research"
        
        # Check query type
        if "details" in query:
            assert result["type"] == "details"
        else:
            assert result["type"] == "search"

@pytest.mark.asyncio
async def test_tools_query_routing(router):
    """Test routing of tool-related queries."""
    # Test various tool queries
    tools_queries = [
        "calculate my biological age",
        "what's my health score",
        "estimate my fitness level",
        "compute my wellness metrics"
    ]
    
    for query in tools_queries:
        result = await router.route_query(query)
        assert result["server"] == "tools"
        
        # Check specific tool types
        if "biological age" in query:
            assert result["type"] == "biological_age"
        elif "health score" in query:
            assert result["type"] == "health_score"

@pytest.mark.asyncio
async def test_unknown_query_routing(router):
    """Test routing of unknown or ambiguous queries."""
    unknown_queries = [
        "hello",
        "what's the weather",
        "help me",
        ""
    ]
    
    for query in unknown_queries:
        result = await router.route_query(query)
        assert result["server"] == "unknown"
        assert result["type"] == "unknown"

@pytest.mark.asyncio
async def test_mixed_query_routing(router):
    """Test routing of queries that might match multiple patterns."""
    mixed_queries = [
        "show me research about health metrics",  # Should prefer research
        "calculate trends in my health data",     # Should prefer health
        "analyze research papers about biological age"  # Should prefer research
    ]
    
    results = [await router.route_query(q) for q in mixed_queries]
    assert results[0]["server"] == "research"  # Research takes precedence
    assert results[1]["server"] == "health"    # Health data analysis
    assert results[2]["server"] == "research"  # Research about bio age 