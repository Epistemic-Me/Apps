"""Tests for the semantic router."""

import pytest
import asyncio
from unittest.mock import MagicMock, patch
from typing import Dict, Any, List
from bio_age_coach.router.semantic_router import SemanticRouter

class MockAgent:
    """Mock agent for testing."""
    
    def __init__(self, name: str, capabilities: List[str], confidence: float = 1.0):
        """Initialize the mock agent.
        
        Args:
            name: Name of the agent
            capabilities: List of capabilities
            confidence: Confidence score to return from can_handle
        """
        self.name = name
        self.capabilities = capabilities
        self._confidence = confidence
        self.domain_examples = capabilities
        self.supported_data_types = set()
        
    async def can_handle(self, query: str, context: Dict[str, Any]) -> float:
        """Determine if this agent can handle the query.
        
        Args:
            query: User query
            context: Conversation context
            
        Returns:
            float: Confidence score between 0 and 1
        """
        return self._confidence
        
    async def process(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process the query and return a response.
        
        Args:
            query: User query
            context: Conversation context
            
        Returns:
            Dict[str, Any]: Response
        """
        return {
            "response": f"Processed by {self.name}",
            "insights": [f"Insight from {self.name}"],
            "visualization": None,
            "error": None
        }
        
    async def create_observation_context(self, data_type: str, data: Dict[str, Any]) -> Any:
        """Create an observation context for the given data type.
        
        Args:
            data_type: Type of data
            data: Data to create context from
            
        Returns:
            Any: Observation context
        """
        return None

@pytest.fixture
def mock_agents():
    """Create mock agents for testing."""
    return [
        MockAgent("BioAgeScoreAgent", [
            "Calculate biological age score",
            "Analyze health metrics",
            "Provide age-related recommendations"
        ]),
        MockAgent("HealthDataAgent", [
            "Process health data",
            "Analyze health metrics",
            "Provide health insights"
        ]),
        MockAgent("ResearchAgent", [
            "Search scientific literature",
            "Provide evidence-based insights",
            "Analyze research findings"
        ])
    ]

@pytest.fixture
def mock_embeddings():
    """Create a mock embeddings object."""
    embeddings = MagicMock()
    embeddings.embed_documents.return_value = [
        [0.1, 0.2, 0.3],
        [0.4, 0.5, 0.6],
        [0.7, 0.8, 0.9]
    ]
    embeddings.embed_query.return_value = [0.1, 0.2, 0.3]
    return embeddings

@pytest.fixture
def mock_vector_store():
    """Create a mock vector store."""
    from langchain.schema import Document
    
    vector_store = MagicMock()
    vector_store.similarity_search_with_score.return_value = [
        (Document(page_content="Calculate biological age score", metadata={"agent_name": "BioAgeScoreAgent"}), 0.1),
        (Document(page_content="Analyze health metrics", metadata={"agent_name": "HealthDataAgent"}), 0.3),
        (Document(page_content="Provide age-related recommendations", metadata={"agent_name": "BioAgeScoreAgent"}), 0.2)
    ]
    return vector_store

@pytest.mark.asyncio
async def test_semantic_router_initialization(mock_agents):
    """Test semantic router initialization."""
    with patch("bio_age_coach.router.semantic_router.OpenAIEmbeddings"):
        with patch("bio_age_coach.router.semantic_router.FAISS"):
            router = SemanticRouter(api_key="test_key", agents=mock_agents)
            
            assert router.api_key == "test_key"
            assert router.agents == mock_agents
            assert router.context == {}
            assert router.route_history == []

@pytest.mark.asyncio
async def test_semantic_route(mock_agents, mock_vector_store):
    """Test semantic routing."""
    with patch("bio_age_coach.router.semantic_router.OpenAIEmbeddings"):
        with patch("bio_age_coach.router.semantic_router.FAISS"):
            router = SemanticRouter(api_key="test_key", agents=mock_agents)
            router.vector_store = mock_vector_store
            
            agent, confidence = await router._semantic_route("What is my biological age?")
            
            assert agent.name == "BioAgeScoreAgent"
            assert confidence > 0.5

@pytest.mark.asyncio
async def test_route_query(mock_agents):
    """Test route_query method."""
    with patch("bio_age_coach.router.semantic_router.OpenAIEmbeddings"):
        with patch("bio_age_coach.router.semantic_router.FAISS"):
            router = SemanticRouter(api_key="test_key", agents=mock_agents)
            
            # Mock _route method
            async def mock_route(query, context):
                return mock_agents[0], 0.9
            
            router._route = mock_route
            
            response = await router.route_query("user1", "What is my biological age?")
            
            assert response["response"] == "Processed by BioAgeScoreAgent"
            assert response["insights"] == ["Insight from BioAgeScoreAgent"]
            assert response["visualization"] is None
            assert response["error"] is None
            assert len(router.route_history) == 1
            assert router.route_history[0]["user_id"] == "user1"
            assert router.route_history[0]["query"] == "What is my biological age?"
            assert router.route_history[0]["selected_agent"] == "BioAgeScoreAgent"
            assert router.route_history[0]["confidence"] == 0.9

@pytest.mark.asyncio
async def test_update_context(mock_agents):
    """Test _update_context method."""
    with patch("bio_age_coach.router.semantic_router.OpenAIEmbeddings"):
        with patch("bio_age_coach.router.semantic_router.FAISS"):
            router = SemanticRouter(api_key="test_key", agents=mock_agents)
            
            router._update_context("user1", "What is my biological age?")
            
            assert "user1" in router.context
            assert len(router.context["user1"]["queries"]) == 1
            assert router.context["user1"]["queries"][0]["text"] == "What is my biological age?"
            
            # Add another query
            router._update_context("user1", "How can I improve my score?", {"key": "value"})
            
            assert len(router.context["user1"]["queries"]) == 2
            assert router.context["user1"]["queries"][1]["text"] == "How can I improve my score?"
            assert router.context["user1"]["queries"][1]["metadata"] == {"key": "value"}
            assert router.context["user1"]["metadata"] == {"key": "value"} 