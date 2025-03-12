"""Shared types and enums for the bio-age-coach package."""

from enum import Enum

class DataCategory(Enum):
    """Categories of test data."""
    DEMOGRAPHICS = "demographics"
    HEALTH_METRICS = "health_metrics"
    FITNESS_METRICS = "fitness_metrics"
    BIOMARKERS = "biomarkers"
    MEASUREMENTS = "measurements"
    LAB_RESULTS = "lab_results" 