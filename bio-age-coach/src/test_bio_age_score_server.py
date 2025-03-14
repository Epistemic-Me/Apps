"""
Test script for BioAgeScoreServer functionality.
"""

import asyncio
import json
import os
import pandas as pd
from datetime import datetime, timedelta
from bio_age_coach.mcp.servers.bio_age_score_server import BioAgeScoreServer
from bio_age_coach.mcp.servers.health_server import HealthServer
from bio_age_coach.types import DataCategory

def process_workout_data(data_dir: str) -> list:
    """Process workout data from Apple Health export files."""
    # Read workout data
    workout_file = os.path.join(data_dir, "Workouts-20250205_000000-20250307_235959.csv")
    df = pd.read_csv(workout_file)
    
    # Convert Start and End columns to datetime
    df['Start'] = pd.to_datetime(df['Start'])
    df['End'] = pd.to_datetime(df['End'])
    df['Date'] = df['Start'].dt.date
    
    # Calculate duration in seconds
    df['Duration'] = (df['End'] - df['Start']).dt.total_seconds()
    
    # Group by date and calculate daily metrics
    daily_metrics = []
    for date, group in df.groupby('Date'):
        # Calculate total active calories (sum of all workouts)
        active_calories = group['Active Energy (kcal)'].sum()
        
        # Calculate total steps (sum of all workouts)
        steps = group['Step Count'].sum()
        
        # Calculate average heart rate (weighted by workout duration)
        weighted_hr = ((group['Avg. Heart Rate (bpm)'] * group['Duration']).sum() / group['Duration'].sum()) if not group['Duration'].empty else 0
        
        # Create daily metrics entry
        metrics = {
            'date': date.strftime('%Y-%m-%d'),
            'active_calories': float(active_calories),
            'steps': float(steps),
            'heart_rate': float(weighted_hr),
            'sleep_hours': 7.5  # Default value for testing
        }
        daily_metrics.append(metrics)
    
    # Sort by date
    daily_metrics = sorted(daily_metrics, key=lambda x: x['date'])
    
    return daily_metrics

async def test_servers():
    """Test the integration of BioAgeScoreServer and HealthServer."""
    print("✓ Initializing test environment...")
    
    # Initialize servers
    api_key = "test_key_123"
    health_server = HealthServer(api_key)
    bio_age_score_server = BioAgeScoreServer(api_key)
    
    # Load test data
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'test_health_data')
    daily_metrics = process_workout_data(data_dir)
    
    # Format health data
    health_data = {"health_data": daily_metrics}
    
    # Initialize servers with test data
    await health_server.initialize_data(health_data)
    await bio_age_score_server.initialize_data(health_data)
    
    # Test daily score calculation
    daily_score = await bio_age_score_server.calculate_daily_score(daily_metrics[0])
    print("\nDaily Score:")
    print(f"Total Score: {daily_score.get('total_score', 0)}")
    print(f"Sleep Score: {daily_score.get('sleep_score', 0)}")
    print(f"Exercise Score: {daily_score.get('exercise_score', 0)}")
    print(f"Steps Score: {daily_score.get('steps_score', 0)}")
    print(f"Insights: {daily_score.get('insights', [])}")
    
    # Test 30-day scores calculation
    thirty_day_scores = await bio_age_score_server.calculate_30_day_scores(daily_metrics)
    print(f"\n30-day Scores: {len(thirty_day_scores)} scores calculated")
    
    # Test visualization creation
    visualization = await bio_age_score_server.create_score_visualization(thirty_day_scores[:-1])
    if visualization:
        print("\nVisualization Data:")
        if "reference_ranges" in visualization:
            print("Reference Ranges:")
            for range_name, range_data in visualization["reference_ranges"].items():
                print(f"  {range_name}: {range_data['min']}-{range_data['max']}")

if __name__ == "__main__":
    asyncio.run(test_servers()) 