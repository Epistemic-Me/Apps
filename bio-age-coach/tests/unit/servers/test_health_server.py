"""Test cases for HealthServer."""

import pytest
from datetime import datetime, timedelta
import os
import json

@pytest.mark.asyncio
async def test_process_workout_data(health_server, test_data_dir):
    """Test processing workout data."""
    # Create test workout data
    workout_data = [
        {
            "Start": "2024-03-01 08:00",
            "Active Energy (kcal)": 400,
            "Step Count": 8000,
            "Avg. Heart Rate (bpm)": 70,
            "Duration": "01:00:00"
        }
    ]
    
    # Save test data
    data_path = os.path.join(test_data_dir, "Workouts-20250205_000000-20250307_235959.csv")
    os.makedirs(test_data_dir, exist_ok=True)
    with open(data_path, "w") as f:
        f.write("Start,Active Energy (kcal),Step Count,Avg. Heart Rate (bpm),Duration\n")
        for workout in workout_data:
            f.write(f"{workout['Start']},{workout['Active Energy (kcal)']},{workout['Step Count']},{workout['Avg. Heart Rate (bpm)']},{workout['Duration']}\n")

    # Initialize test data path
    init_request = {
        "api_key": "test_api_key",
        "type": "initialize_data",
        "data": {
            "test_data_path": test_data_dir
        }
    }
    await health_server.handle_request(init_request)

    # Process workout data
    request = {
        "api_key": "test_api_key",
        "type": "process_workout_data",
        "data": {
            "data_dir": test_data_dir
        }
    }

    response = await health_server.handle_request(request)
    assert "error" not in response
    assert isinstance(response, list)
    assert len(response) > 0
    
    # Check data structure and reasonable ranges
    first_metric = response[0]
    assert "active_calories" in first_metric
    assert "steps" in first_metric
    assert "heart_rate" in first_metric
    assert "date" in first_metric
    assert 300 <= first_metric["active_calories"] <= 700  # Reasonable range
    assert 6000 <= first_metric["steps"] <= 12000  # Reasonable range
    assert 60 <= first_metric["heart_rate"] <= 80  # Reasonable range

@pytest.mark.asyncio
async def test_aggregate_metrics(health_server):
    """Test aggregating health metrics."""
    workouts = [
        {
            "date": "2024-03-01",
            "active_calories": 400,
            "steps": 8000,
            "heart_rate": 70,
            "workout_count": 1
        },
        {
            "date": "2024-03-01",
            "active_calories": 300,
            "steps": 6000,
            "heart_rate": 75,
            "workout_count": 1
        }
    ]

    request = {
        "api_key": "test_api_key",
        "type": "aggregate_metrics",
        "data": {
            "metrics": {
                "workouts": workouts
            }
        }
    }

    response = await health_server.handle_request(request)
    assert "error" not in response
    assert isinstance(response, dict)
    assert "metrics" in response
    assert "2024-03-01" in response["metrics"]
    metrics = response["metrics"]["2024-03-01"]
    assert metrics["active_calories"] == 700
    assert metrics["steps"] == 14000
    assert metrics["heart_rate"] == 72.5
    assert metrics["workout_count"] == 2

@pytest.mark.asyncio
async def test_get_metrics(health_server, test_data_dir):
    """Test getting health metrics."""
    # First initialize test data
    await test_process_workout_data(health_server, test_data_dir)

    request = {
        "api_key": "test_api_key",
        "type": "metrics",
        "timeframe": "30D"
    }

    response = await health_server.handle_request(request)
    assert "error" not in response
    assert "metrics" in response
    assert "workouts" in response
    assert isinstance(response["metrics"], list)
    assert isinstance(response["workouts"], list)
    assert len(response["workouts"]) > 0
    # Check the raw workout data format
    workout = response["workouts"][0]
    assert "date" in workout
    assert "active_calories" in workout
    assert "steps" in workout
    assert "heart_rate" in workout
    assert "workout_count" in workout

@pytest.mark.asyncio
async def test_list_resources(health_server):
    """Test listing available resources."""
    request = {
        "api_key": "test_api_key",
        "type": "resources/list"
    }

    response = await health_server.handle_request(request)
    assert "error" not in response
    assert "resources" in response
    assert "resourceTemplates" in response
    assert isinstance(response["resources"], list)
    assert isinstance(response["resourceTemplates"], list)
    assert len(response["resources"]) == 3  # workouts, daily_metrics, heart_rate
    assert len(response["resourceTemplates"]) == 2  # workout_by_date, metrics_by_date

@pytest.mark.asyncio
async def test_read_resource(health_server, test_data_dir):
    """Test reading a specific resource."""
    # First initialize test data
    await test_process_workout_data(health_server, test_data_dir)

    request = {
        "api_key": "test_api_key",
        "type": "resources/read",
        "uri": "health://data/workouts"
    }

    response = await health_server.handle_request(request)
    assert "error" not in response
    assert "contents" in response
    assert isinstance(response["contents"], list)
    assert len(response["contents"]) > 0
    assert "uri" in response["contents"][0]
    assert "mimeType" in response["contents"][0]
    assert "text" in response["contents"][0]
    workouts = eval(response["contents"][0]["text"])
    assert len(workouts) > 0
    # Check the raw workout data format
    assert "date" in workouts[0]
    assert "active_calories" in workouts[0]
    assert "steps" in workouts[0]
    assert "heart_rate" in workouts[0]
    assert "workout_count" in workouts[0]

@pytest.mark.asyncio
async def test_read_resource_by_date(health_server, test_data_dir):
    """Test reading a resource by date."""
    # Create test workout data for a specific date
    workout_data = [
        {
            "date": "2024-03-01",
            "active_calories": 400,
            "steps": 8000,
            "heart_rate": 70,
            "workout_count": 1
        }
    ]

    # Save test data
    data_path = os.path.join(test_data_dir, "Workouts-20240301_000000-20240301_235959.csv")  # Changed date format
    os.makedirs(test_data_dir, exist_ok=True)
    with open(data_path, "w") as f:
        f.write("date,active_calories,steps,heart_rate,workout_count\n")
        for workout in workout_data:
            f.write(f"{workout['date']},{workout['active_calories']},{workout['steps']},{workout['heart_rate']},{workout['workout_count']}\n")

    # Initialize test data path
    init_request = {
        "api_key": "test_api_key",
        "type": "initialize_data",
        "data": {
            "test_data_path": test_data_dir
        }
    }
    await health_server.handle_request(init_request)

    # Process workout data
    process_request = {
        "api_key": "test_api_key",
        "type": "process_workout_data",
        "data": {
            "data_dir": test_data_dir
        }
    }
    await health_server.handle_request(process_request)

    # Test reading workouts for the specific date
    request = {
        "api_key": "test_api_key",
        "type": "resources/read",
        "uri": "health://data/workouts/2024-03-01"
    }

    response = await health_server.handle_request(request)
    assert "error" not in response
    assert "contents" in response
    assert isinstance(response["contents"], list)
    assert len(response["contents"]) > 0
    assert "uri" in response["contents"][0]
    assert "mimeType" in response["contents"][0]
    assert "text" in response["contents"][0]
    workouts = eval(response["contents"][0]["text"])
    assert len(workouts) > 0
    assert workouts[0]["date"] == "2024-03-01"
    # Check the raw workout data format
    assert "date" in workouts[0]
    assert "active_calories" in workouts[0]
    assert "steps" in workouts[0]
    assert "heart_rate" in workouts[0]
    assert "workout_count" in workouts[0]

@pytest.mark.asyncio
async def test_invalid_request_type(health_server):
    """Test handling of invalid request type."""
    request = {
        "api_key": "test_api_key",
        "type": "invalid_type"
    }

    response = await health_server.handle_request(request)
    assert "error" in response
    assert "Unknown request type" in response["error"]

@pytest.mark.asyncio
async def test_authentication(health_server):
    """Test request authentication."""
    request = {
        "api_key": "wrong_key",
        "type": "metrics"
    }

    response = await health_server.handle_request(request)
    assert "error" in response
    assert "Authentication failed" in response["error"]