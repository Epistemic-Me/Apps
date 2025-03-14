"""Test cases for BioAgeScoreServer."""

import pytest
from datetime import datetime, timedelta
import os
import json

@pytest.mark.asyncio
async def test_calculate_daily_score(bio_age_score_server):
    """Test calculating daily score."""
    request = {
        "api_key": "test_api_key",
        "type": "calculate_daily_score",
        "metrics": {
            "health_data": {
                "sleep_hours": 7.5,
                "active_calories": 400,
                "steps": 8000
            }
        }
    }

    response = await bio_age_score_server.handle_request(request)
    assert "error" not in response
    assert "total_score" in response
    assert "sleep_score" in response
    assert "exercise_score" in response
    assert "steps_score" in response

@pytest.mark.asyncio
async def test_calculate_30_day_scores(bio_age_score_server):
    """Test calculating 30-day scores."""
    # Create 30 days of test data
    health_data_series = [
        {
            "date": (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d"),
            "sleep_hours": 7.5,
            "active_calories": 400,
            "steps": 8000
        }
        for i in range(30)
    ]

    request = {
        "api_key": "test_api_key",
        "type": "calculate_30_day_scores",
        "metrics": {
            "health_data_series": health_data_series
        }
    }

    response = await bio_age_score_server.handle_request(request)
    assert "error" not in response
    assert isinstance(response, list)
    assert len(response) > 0

@pytest.mark.asyncio
async def test_create_visualization(bio_age_score_server):
    """Test creating score visualization."""
    scores = [
        {
            "date": (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d"),
            "total_score": 85 + i,
            "sleep_score": 50,
            "exercise_score": 20,
            "steps_score": 15
        }
        for i in range(7)
    ]

    request = {
        "api_key": "test_api_key",
        "type": "create_visualization",
        "data": {
            "scores": scores
        }
    }

    response = await bio_age_score_server.handle_request(request)
    assert "error" not in response
    assert "visualization" in response
    assert "insights" in response

@pytest.mark.asyncio
async def test_invalid_request_type(bio_age_score_server):
    """Test handling of invalid request type."""
    request = {
        "api_key": "test_api_key",
        "type": "invalid_type"
    }

    response = await bio_age_score_server.handle_request(request)
    assert "error" in response
    assert "Unknown request type" in response["error"]

@pytest.mark.asyncio
async def test_authentication(bio_age_score_server):
    """Test request authentication."""
    request = {
        "api_key": "wrong_key",
        "type": "calculate_daily_score",
        "metrics": {
            "health_data": {
                "sleep_hours": 7.5,
                "active_calories": 400,
                "steps": 8000
            }
        }
    }

    response = await bio_age_score_server.handle_request(request)
    assert "error" in response
    assert "Authentication failed" in response["error"]

@pytest.mark.asyncio
async def test_invalid_metrics_format(bio_age_score_server):
    """Test handling of invalid metrics format."""
    request = {
        "api_key": "test_api_key",
        "type": "calculate_daily_score",
        "metrics": {
            "health_data": "invalid_format"
        }
    }

    response = await bio_age_score_server.handle_request(request)
    assert "error" in response
    assert "Expected dictionary" in response["error"] 