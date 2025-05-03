"""
Standardized test data for evaluations.
"""

from typing import Dict, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
from bio_age_coach.types import DataCategory

class DataCategory(Enum):
    DEMOGRAPHICS = "demographics"
    HEALTH_METRICS = "health_metrics"
    FITNESS_METRICS = "fitness_metrics"
    BIOMARKERS = "biomarkers"
    MEASUREMENTS = "measurements"
    LAB_RESULTS = "lab_results"

@dataclass
class TestUserProfile:
    """Standard test user profile for evaluations."""
    age: int = 18
    sex: str = "male"
    height: float = 175.0  # cm
    weight: float = 70.0   # kg

@dataclass
class TestHealthMetrics:
    """Standard health metrics for evaluations."""
    active_calories: int = 400
    steps: int = 8000
    sleep_hours: float = 6.5
    resting_heart_rate: int = 65
    blood_pressure_systolic: int = 120
    blood_pressure_diastolic: int = 80

@dataclass
class TestFitnessMetrics:
    """Standard fitness metrics for evaluations."""
    push_ups: int = 15
    grip_strength: float = 90.0
    one_leg_stand: int = 45
    plank: int = 120
    sit_and_reach: int = 15

@dataclass
class TestBiomarkers:
    """Standard biomarkers for evaluations."""
    hba1c: float = 5.9
    fasting_glucose: int = 105
    hdl: int = 65
    ldl: int = 100
    triglycerides: int = 150
    crp: float = 1.5

@dataclass
class TestMeasurements:
    """Standard body measurements for evaluations."""
    body_fat: float = 18.5
    waist_circumference: float = 82.0
    hip_circumference: float = 98.0
    waist_to_hip: float = 0.84

@dataclass
class TestLabResults:
    """Standard lab results for evaluations."""
    vitamin_d: int = 45

def create_test_data() -> Dict[str, Any]:
    """Create a standard set of test data."""
    # Get current date for test data
    current_date = datetime.now()
    
    # Create daily metrics for the past week
    daily_metrics = {
        "steps": [],
        "active_calories": [],
        "heart_rate": [],
        "distance": []
    }
    
    for i in range(7):
        date = current_date - timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")
        
        # Add steps data
        daily_metrics["steps"].append({
            "startDate": date_str,
            "value": 8000 + (i * 100)  # Varying step counts
        })
        
        # Add active calories data
        daily_metrics["active_calories"].append({
            "startDate": date_str,
            "value": 450  # Consistent value for testing
        })
        
        # Add heart rate data
        daily_metrics["heart_rate"].append({
            "startDate": date_str,
            "value": 65 + (i % 3)  # Slightly varying heart rate
        })
        
        # Add distance data
        daily_metrics["distance"].append({
            "startDate": date_str,
            "value": 5.0 + (i * 0.1)  # Varying distance
        })
    
    return {
        DataCategory.DEMOGRAPHICS.value: {
            "age": 18,
            "sex": "male",
            "height": 175,
            "weight": 70
        },
        DataCategory.HEALTH_METRICS.value: {
            "active_calories": 450,
            "steps": 8000,
            "heart_rate": 65,
            "sleep_hours": 7.5,
            "daily_metrics": daily_metrics
        },
        DataCategory.FITNESS_METRICS.value: {
            "push_ups": 15,
            "grip_strength": 90.0,
            "vo2_max": 45.5
        },
        DataCategory.BIOMARKERS.value: {
            "hba1c": 5.9,
            "fasting_glucose": 105,
            "crp": 1.2
        },
        DataCategory.MEASUREMENTS.value: {
            "blood_pressure_systolic": 120,
            "blood_pressure_diastolic": 80,
            "resting_heart_rate": 65
        },
        DataCategory.LAB_RESULTS.value: {
            "vitamin_d": 45,
            "testosterone": 600,
            "cortisol": 15
        }
    }

def create_variant_test_data(category: DataCategory, **kwargs) -> Dict[str, Any]:
    """Create a variant of the standard test data with specific modifications."""
    base_data = create_test_data()
    
    if category.value in base_data:
        base_data[category.value].update(kwargs)
    
    return base_data 