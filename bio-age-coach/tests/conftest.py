"""Common test fixtures and utilities for bio-age-coach tests."""

import os
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from bio_age_coach.mcp.servers.bio_age_score_server import BioAgeScoreServer
from bio_age_coach.mcp.servers.health_server import HealthServer
from bio_age_coach.mcp.servers.research_server import ResearchServer
from bio_age_coach.mcp.servers.tools_server import ToolsServer
from bio_age_coach.router.semantic_router import SemanticRouter
from bio_age_coach.router.router_adapter import RouterAdapter
from bio_age_coach.mcp.client import MultiServerMCPClient
from bio_age_coach.agents.specialized.bio_age_score_agent import BioAgeScoreAgent

@pytest.fixture
def test_api_key():
    """Provide a test API key."""
    return "test_api_key"

@pytest.fixture
def test_data_dir():
    """Provide the test data directory path."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, "tests", "test_data")

@pytest.fixture
async def bio_age_score_server(test_api_key, test_data_dir):
    """Create a bio age score server instance with test data."""
    data_path = os.path.join(test_data_dir, "bio_age_score")
    os.makedirs(data_path, exist_ok=True)
    server = BioAgeScoreServer(test_api_key)
    await server.initialize_data({})
    return server

@pytest.fixture
async def health_server(test_api_key, test_data_dir):
    """Create a health server instance with test data."""
    data_path = os.path.join(test_data_dir, "health")
    os.makedirs(data_path, exist_ok=True)
    server = HealthServer(test_api_key)
    await server.initialize_data({})
    return server

@pytest.fixture
async def research_server(test_api_key, test_data_dir):
    """Create a research server instance with test data."""
    data_path = os.path.join(test_data_dir, "research")
    os.makedirs(data_path, exist_ok=True)
    server = ResearchServer(test_api_key)
    await server.initialize_data({})
    return server

@pytest.fixture
async def tools_server(test_api_key, test_data_dir):
    """Create a tools server instance with test data."""
    data_path = os.path.join(test_data_dir, "tools")
    os.makedirs(data_path, exist_ok=True)
    server = ToolsServer(test_api_key)
    await server.initialize_data({})
    return server

@pytest.fixture
async def mcp_client(test_api_key, bio_age_score_server, health_server, research_server, tools_server):
    """Create a MultiServerMCPClient instance with all servers."""
    client = MultiServerMCPClient(api_key=test_api_key)
    client.register_server("bio_age_score", bio_age_score_server)
    client.register_server("health", health_server)
    client.register_server("research", research_server)
    client.register_server("tools", tools_server)
    return client

@pytest.fixture
async def test_agents(test_api_key, mcp_client):
    """Create test agents for the semantic router."""
    bio_age_score_agent = BioAgeScoreAgent(
        name="BioAgeScoreAgent",
        description="I analyze health metrics to calculate and explain biological age scores.",
        api_key=test_api_key,
        mcp_client=mcp_client
    )
    return [bio_age_score_agent]

@pytest.fixture
async def semantic_router(test_api_key, test_agents):
    """Create a SemanticRouter instance with test agents."""
    # Create a mock for the SemanticRouter class
    with patch('bio_age_coach.router.semantic_router.OpenAIEmbeddings') as mock_embeddings, \
         patch('bio_age_coach.router.semantic_router.FAISS') as mock_faiss, \
         patch('bio_age_coach.router.semantic_router.AsyncOpenAI') as mock_openai:
        
        # Configure the mock embeddings
        mock_embeddings.return_value.embed_documents.return_value = [[0.1, 0.2, 0.3] for _ in range(10)]
        mock_embeddings.return_value.embed_query.return_value = [0.1, 0.2, 0.3]
        
        # Configure the mock FAISS
        mock_faiss.from_documents.return_value.similarity_search_with_score.return_value = [
            (MagicMock(page_content="Test content", metadata={"agent_name": "BioAgeScoreAgent"}), 0.9)
        ]
        
        # Create the router with the mocked dependencies
        router = SemanticRouter(api_key=test_api_key, agents=test_agents)
        
        # Mock the _route method to return the first agent
        async def mock_route(query, context):
            if test_agents:
                return test_agents[0], 0.9
            return None, 0.0
            
        router._route = AsyncMock(side_effect=mock_route)
        
        return router

@pytest.fixture
async def router_adapter(semantic_router, mcp_client):
    """Create a RouterAdapter instance with the semantic router."""
    return RouterAdapter(semantic_router=semantic_router, mcp_client=mcp_client)

@pytest.fixture
def sample_health_data():
    """Provide sample health data for testing."""
    return {
        "sleep_hours": 7.5,
        "active_calories": 400,
        "steps": 8000,
        "heart_rate": 70
    }

@pytest.fixture
def sample_research_data():
    """Provide sample research data for testing."""
    return {
        "papers": [
            {
                "id": "paper1",
                "title": "Exercise and Longevity",
                "abstract": "Study on effects of exercise on longevity.",
                "keywords": ["exercise", "longevity", "health"],
                "year": 2023,
                "authors": ["Smith, J.", "Jones, K."]
            }
        ]
    } 