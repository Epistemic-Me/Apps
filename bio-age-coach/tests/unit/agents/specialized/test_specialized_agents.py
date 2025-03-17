"""Tests for specialized agent classes."""

import pytest
from unittest.mock import Mock, AsyncMock
from bio_age_coach.agents.base_agent import AgentState
from bio_age_coach.mcp.client import MultiServerMCPClient
from typing import Dict, Any, List, Set, Optional
from langchain.tools import BaseTool

# Mock implementations of specialized agents for testing
class MockBioAgeScoreAgent:
    """Mock implementation of BioAgeScoreAgent for testing."""
    
    def __init__(
        self,
        name: str,
        api_key: str,
        mcp_client,
        tools: Optional[List[BaseTool]] = None,
        **kwargs
    ):
        self.name = name
        self.description = "I analyze health metrics to calculate and explain biological age scores."
        self.api_key = api_key
        self.mcp_client = mcp_client
        self.tools = tools or []
        self.state = {"state": AgentState.READY}
        self.capabilities = []
        self.server_types = set()
        self._initialize_capabilities()
        self._initialize_servers()
    
    def _initialize_capabilities(self) -> None:
        self.capabilities = [
            "Calculate biological age score",
            "Analyze health metrics",
            "Provide age-related recommendations",
            "Track bio-age trends"
        ]
    
    def _initialize_servers(self) -> None:
        self.server_types = {"bio_age_score"}
    
    async def can_handle(self, query: str, context: Dict[str, Any]) -> float:
        keywords = ["bio age", "biological age", "age score", "health age"]
        return 1.0 if any(keyword in query.lower() for keyword in keywords) else 0.0
    
    async def process(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "response": "I'll help you understand your biological age score.",
            "insights": ["Your biological age is being calculated based on your health metrics."],
            "visualization": None,
            "error": None
        }

class MockBioAgeTestsAgent:
    """Mock implementation of BioAgeTestsAgent for testing."""
    
    def __init__(
        self,
        name: str,
        api_key: str,
        mcp_client,
        tools: Optional[List[BaseTool]] = None,
        **kwargs
    ):
        self.name = name
        self.description = "I help you track and analyze functional tests like grip strength and push-up capacity."
        self.api_key = api_key
        self.mcp_client = mcp_client
        self.tools = tools or []
        self.state = {"state": AgentState.READY}
        self.capabilities = []
        self.server_types = set()
        self._initialize_capabilities()
        self._initialize_servers()
    
    def _initialize_capabilities(self) -> None:
        self.capabilities = [
            "Track grip strength",
            "Monitor push-up capacity",
            "Record sit-to-stand test results",
            "Analyze functional test trends"
        ]
    
    def _initialize_servers(self) -> None:
        self.server_types = {"bio_age_tests"}
    
    async def can_handle(self, query: str, context: Dict[str, Any]) -> float:
        keywords = ["functional test", "grip strength", "push-up", "sit-to-stand"]
        return 1.0 if any(keyword in query.lower() for keyword in keywords) else 0.0
    
    async def process(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "response": "I'll help you track your functional tests.",
            "insights": ["Your functional test results are being analyzed."],
            "visualization": None,
            "error": None
        }

class MockCapabilitiesAgent:
    """Mock implementation of CapabilitiesAgent for testing."""
    
    def __init__(
        self,
        name: str,
        api_key: str,
        mcp_client,
        tools: Optional[List[BaseTool]] = None,
        **kwargs
    ):
        self.name = name
        self.description = "I help you track and analyze physical capabilities like strength, endurance, and flexibility."
        self.api_key = api_key
        self.mcp_client = mcp_client
        self.tools = tools or []
        self.state = {"state": AgentState.READY}
        self.capabilities = []
        self.server_types = set()
        self._initialize_capabilities()
        self._initialize_servers()
    
    def _initialize_capabilities(self) -> None:
        self.capabilities = [
            "Track strength metrics",
            "Monitor endurance metrics",
            "Record flexibility metrics",
            "Analyze capability trends"
        ]
    
    def _initialize_servers(self) -> None:
        self.server_types = {"capabilities"}
    
    async def can_handle(self, query: str, context: Dict[str, Any]) -> float:
        keywords = ["strength", "endurance", "flexibility", "physical capability", "workout capacity"]
        return 1.0 if any(keyword in query.lower() for keyword in keywords) else 0.0
    
    async def process(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "response": "I'll help you track your physical capabilities.",
            "insights": ["Your physical capability metrics are being analyzed."],
            "visualization": None,
            "error": None
        }

class MockBiomarkersAgent:
    """Mock implementation of BiomarkersAgent for testing."""
    
    def __init__(
        self,
        name: str,
        api_key: str,
        mcp_client,
        tools: Optional[List[BaseTool]] = None,
        **kwargs
    ):
        self.name = name
        self.description = "I help you track and analyze biomarkers like blood glucose, HbA1c, and cholesterol."
        self.api_key = api_key
        self.mcp_client = mcp_client
        self.tools = tools or []
        self.state = {"state": AgentState.READY}
        self.capabilities = []
        self.server_types = set()
        self._initialize_capabilities()
        self._initialize_servers()
    
    def _initialize_capabilities(self) -> None:
        self.capabilities = [
            "Track blood glucose",
            "Monitor HbA1c",
            "Record cholesterol levels",
            "Analyze biomarker trends"
        ]
    
    def _initialize_servers(self) -> None:
        self.server_types = {"biomarkers"}
    
    async def can_handle(self, query: str, context: Dict[str, Any]) -> float:
        keywords = ["blood test", "urine test", "biomarker", "lab result", "blood glucose", "glucose", "HbA1c", "cholesterol"]
        return 1.0 if any(keyword in query.lower() for keyword in keywords) else 0.0
    
    async def process(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "response": "I'll help you track your biomarker test results.",
            "insights": ["Your biomarker test results are being analyzed."],
            "visualization": None,
            "error": None
        }

class MockMeasurementsAgent:
    """Mock implementation of MeasurementsAgent for testing."""
    
    def __init__(
        self,
        name: str,
        api_key: str,
        mcp_client,
        tools: Optional[List[BaseTool]] = None,
        **kwargs
    ):
        self.name = name
        self.description = "I help you track and analyze physical measurements like weight, body fat, and waist circumference."
        self.api_key = api_key
        self.mcp_client = mcp_client
        self.tools = tools or []
        self.state = {"state": AgentState.READY}
        self.capabilities = []
        self.server_types = set()
        self._initialize_capabilities()
        self._initialize_servers()
    
    def _initialize_capabilities(self) -> None:
        self.capabilities = [
            "Track weight changes",
            "Monitor body fat percentage",
            "Record body measurements",
            "Analyze measurement trends"
        ]
    
    def _initialize_servers(self) -> None:
        self.server_types = {"measurements"}
    
    async def can_handle(self, query: str, context: Dict[str, Any]) -> float:
        keywords = ["weight", "body fat", "waist", "measurement", "inches", "centimeters"]
        return 1.0 if any(keyword in query.lower() for keyword in keywords) else 0.0
    
    async def process(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "response": "I'll help you track your physical measurements.",
            "insights": ["Your measurement data is being analyzed."],
            "visualization": None,
            "error": None
        }

class MockLabResultsAgent:
    """Mock implementation of LabResultsAgent for testing."""
    
    def __init__(
        self,
        name: str,
        api_key: str,
        mcp_client,
        tools: Optional[List[BaseTool]] = None,
        **kwargs
    ):
        self.name = name
        self.description = "I help you track and analyze laboratory test results."
        self.api_key = api_key
        self.mcp_client = mcp_client
        self.tools = tools or []
        self.state = {"state": AgentState.READY}
        self.capabilities = []
        self.server_types = set()
        self._initialize_capabilities()
        self._initialize_servers()
    
    def _initialize_capabilities(self) -> None:
        self.capabilities = [
            "Track blood test results",
            "Monitor urine test results",
            "Record specialized test results",
            "Analyze lab result trends"
        ]
    
    def _initialize_servers(self) -> None:
        self.server_types = {"lab_results"}
    
    async def can_handle(self, query: str, context: Dict[str, Any]) -> float:
        keywords = ["blood test", "urine test", "lab result", "laboratory"]
        return 1.0 if any(keyword in query.lower() for keyword in keywords) else 0.0
    
    async def process(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "response": "I'll help you track your laboratory test results.",
            "insights": ["Your lab test results are being analyzed."],
            "visualization": None,
            "error": None
        }

@pytest.fixture
def mock_mcp_client():
    """Create a mock MCP client."""
    client = Mock(spec=MultiServerMCPClient)
    client.send_request = AsyncMock(return_value={"result": "test"})
    return client

@pytest.fixture
def bio_age_score_agent(mock_mcp_client):
    """Create a BioAgeScoreAgent instance."""
    return MockBioAgeScoreAgent(
        name="bio_age_score",
        api_key="test_key",
        mcp_client=mock_mcp_client
    )

@pytest.fixture
def bio_age_tests_agent(mock_mcp_client):
    """Create a BioAgeTestsAgent instance."""
    return MockBioAgeTestsAgent(
        name="bio_age_tests",
        api_key="test_key",
        mcp_client=mock_mcp_client
    )

@pytest.fixture
def capabilities_agent(mock_mcp_client):
    """Create a CapabilitiesAgent instance."""
    return MockCapabilitiesAgent(
        name="capabilities",
        api_key="test_key",
        mcp_client=mock_mcp_client
    )

@pytest.fixture
def biomarkers_agent(mock_mcp_client):
    """Create a BiomarkersAgent instance."""
    return MockBiomarkersAgent(
        name="biomarkers",
        api_key="test_key",
        mcp_client=mock_mcp_client
    )

@pytest.fixture
def measurements_agent(mock_mcp_client):
    """Create a MeasurementsAgent instance."""
    return MockMeasurementsAgent(
        name="measurements",
        api_key="test_key",
        mcp_client=mock_mcp_client
    )

@pytest.fixture
def lab_results_agent(mock_mcp_client):
    """Create a LabResultsAgent instance."""
    return MockLabResultsAgent(
        name="lab_results",
        api_key="test_key",
        mcp_client=mock_mcp_client
    )

@pytest.mark.asyncio
async def test_bio_age_score_agent_initialization(bio_age_score_agent):
    """Test BioAgeScoreAgent initialization."""
    assert bio_age_score_agent.name == "bio_age_score"
    assert "biological age" in bio_age_score_agent.description.lower()
    assert "bio_age_score" in bio_age_score_agent.server_types
    assert len(bio_age_score_agent.capabilities) == 4

@pytest.mark.asyncio
async def test_bio_age_score_agent_can_handle(bio_age_score_agent):
    """Test BioAgeScoreAgent can_handle method."""
    assert await bio_age_score_agent.can_handle("What is my biological age?", {}) == 1.0
    assert await bio_age_score_agent.can_handle("How many steps did I take?", {}) == 0.0

@pytest.mark.asyncio
async def test_bio_age_tests_agent_initialization(bio_age_tests_agent):
    """Test BioAgeTestsAgent initialization."""
    assert bio_age_tests_agent.name == "bio_age_tests"
    assert "functional tests" in bio_age_tests_agent.description.lower()
    assert "bio_age_tests" in bio_age_tests_agent.server_types
    assert len(bio_age_tests_agent.capabilities) == 4

@pytest.mark.asyncio
async def test_bio_age_tests_agent_can_handle(bio_age_tests_agent):
    """Test BioAgeTestsAgent can_handle method."""
    assert await bio_age_tests_agent.can_handle("What is my grip strength?", {}) == 1.0
    assert await bio_age_tests_agent.can_handle("How many steps did I take?", {}) == 0.0

@pytest.mark.asyncio
async def test_capabilities_agent_initialization(capabilities_agent):
    """Test CapabilitiesAgent initialization."""
    assert capabilities_agent.name == "capabilities"
    assert "physical capabilities" in capabilities_agent.description.lower()
    assert "capabilities" in capabilities_agent.server_types
    assert len(capabilities_agent.capabilities) == 4

@pytest.mark.asyncio
async def test_capabilities_agent_can_handle(capabilities_agent):
    """Test CapabilitiesAgent can_handle method."""
    assert await capabilities_agent.can_handle("How is my strength?", {}) == 1.0
    assert await capabilities_agent.can_handle("What is my biological age?", {}) == 0.0

@pytest.mark.asyncio
async def test_biomarkers_agent_initialization(biomarkers_agent):
    """Test BiomarkersAgent initialization."""
    assert biomarkers_agent.name == "biomarkers"
    assert "biomarkers" in biomarkers_agent.description.lower()
    assert "biomarkers" in biomarkers_agent.server_types
    assert len(biomarkers_agent.capabilities) == 4

@pytest.mark.asyncio
async def test_biomarkers_agent_can_handle(biomarkers_agent):
    """Test BiomarkersAgent can_handle method."""
    assert await biomarkers_agent.can_handle("What is my blood glucose?", {}) == 1.0
    assert await biomarkers_agent.can_handle("What is my biological age?", {}) == 0.0

@pytest.mark.asyncio
async def test_measurements_agent_initialization(measurements_agent):
    """Test MeasurementsAgent initialization."""
    assert measurements_agent.name == "measurements"
    assert "measurements" in measurements_agent.description.lower()
    assert "measurements" in measurements_agent.server_types
    assert len(measurements_agent.capabilities) == 4

@pytest.mark.asyncio
async def test_measurements_agent_can_handle(measurements_agent):
    """Test MeasurementsAgent can_handle method."""
    assert await measurements_agent.can_handle("What is my weight?", {}) == 1.0
    assert await measurements_agent.can_handle("What is my biological age?", {}) == 0.0

@pytest.mark.asyncio
async def test_lab_results_agent_initialization(lab_results_agent):
    """Test LabResultsAgent initialization."""
    assert lab_results_agent.name == "lab_results"
    assert "laboratory test" in lab_results_agent.description.lower()
    assert "lab_results" in lab_results_agent.server_types
    assert len(lab_results_agent.capabilities) == 4

@pytest.mark.asyncio
async def test_lab_results_agent_can_handle(lab_results_agent):
    """Test LabResultsAgent can_handle method."""
    assert await lab_results_agent.can_handle("What are my blood test results?", {}) == 1.0
    assert await lab_results_agent.can_handle("What is my biological age?", {}) == 0.0

@pytest.mark.asyncio
async def test_agent_process_methods(
    bio_age_score_agent, bio_age_tests_agent, capabilities_agent,
    biomarkers_agent, measurements_agent, lab_results_agent
):
    """Test process methods for all agents."""
    agents = [
        bio_age_score_agent, bio_age_tests_agent, capabilities_agent,
        biomarkers_agent, measurements_agent, lab_results_agent
    ]
    
    for agent in agents:
        response = await agent.process("test query", {})
        assert "response" in response
        assert "insights" in response
        assert "visualization" in response
        assert "error" in response 