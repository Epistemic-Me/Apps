"""
Tests for MCP server data loading and initialization.
"""

import os
import json
import pytest
import asyncio
from pathlib import Path
from typing import Dict, Any
import pandas as pd
from bio_age_coach.mcp.data_manager import MCPDataManager
from .test_data import create_test_data, DataCategory

@pytest.fixture
async def test_data_manager():
    """Create a test data manager with a temporary test directory."""
    test_dir = "data/test"
    manager = MCPDataManager(test_dir)
    yield manager
    # Cleanup test files after tests
    for path in [manager.health_data_dir, manager.research_data_dir, manager.tools_data_dir]:
        if path.exists():
            for file in path.glob("*"):
                file.unlink()
            path.rmdir()
    Path(test_dir).rmdir()

async def test_data_initialization(test_data_manager):
    """Test that test data is properly initialized in the MCP servers."""
    try:
        # Initialize test data
        test_data = create_test_data()
        await test_data_manager.initialize_test_data(test_data)
        
        # Verify health data
        health_data_path = test_data_manager.health_data_dir / "test_health_data.csv"
        assert health_data_path.exists(), "Health data file not created"
        health_data = pd.read_csv(health_data_path).to_dict(orient="records")[0]
        assert health_data["active_calories"] == test_data[DataCategory.HEALTH_METRICS.value]["active_calories"]
        
        # Verify research data
        papers_path = test_data_manager.research_data_dir / "test_papers.json"
        assert papers_path.exists(), "Research papers file not created"
        with open(papers_path) as f:
            papers_data = json.load(f)
        assert "biomarkers" in papers_data, "Research data missing biomarkers section"
        
        # Verify tools data
        tools_path = test_data_manager.tools_data_dir / "test_tools_config.json"
        assert tools_path.exists(), "Tools config file not created"
        with open(tools_path) as f:
            tools_data = json.load(f)
        assert "biological_age" in tools_data, "Tools data missing biological age config"
    except Exception as e:
        pytest.fail(f"Test failed with error: {str(e)}")

async def test_server_initialization(test_data_manager):
    """Test that MCP servers are properly initialized with test data."""
    api_key = os.getenv("OPENAI_API_KEY", "test_key")
    
    # Initialize test data
    test_data = create_test_data()
    await test_data_manager.initialize_test_data(test_data)
    
    # Initialize servers
    servers = await MCPDataManager.initialize_servers(api_key, test_data_manager.data_dir)
    
    # Verify health server data
    health_server = servers["health"]
    health_data = await health_server.get_user_data("test_user")
    assert health_data is not None, "Health server data not initialized"
    assert "health_data" in health_data, "Health data missing from user data"
    assert health_data["health_data"]["active_calories"] == test_data[DataCategory.HEALTH_METRICS.value]["active_calories"]
    
    # Verify research server data
    research_server = servers["research"]
    papers = await research_server.get_papers("biomarkers")
    assert papers is not None, "Research server data not initialized"
    assert len(papers) > 0, "No papers loaded in research server"
    
    # Verify tools server data
    tools_server = servers["tools"]
    config = await tools_server.get_config()
    assert config is not None, "Tools server data not initialized"
    assert "biological_age" in config, "Tools server missing biological age config"

async def test_data_updates(test_data_manager):
    """Test that data updates are properly handled by MCP servers."""
    # Initialize with original data
    test_data = create_test_data()
    await test_data_manager.initialize_test_data(test_data)
    
    # Update health metrics
    updated_health_data = {
        "health_data": {
            "active_calories": 500,
            "steps": 10000
        }
    }
    await test_data_manager.update_server_data("health", updated_health_data)
    
    # Verify update
    loaded_data = await test_data_manager.load_server_data("health")
    assert loaded_data["health_data"]["active_calories"] == 500, "Health data update failed"

if __name__ == "__main__":
    asyncio.run(pytest.main([__file__])) 