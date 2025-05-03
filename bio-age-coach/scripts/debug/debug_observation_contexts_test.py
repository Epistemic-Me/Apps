"""
Test script to check if observation contexts are being created correctly.
"""

import asyncio
import os
from dotenv import load_dotenv
from bio_age_coach.router.observation_context import (
    ObservationContext,
    SleepObservationContext,
    ExerciseObservationContext,
    NutritionObservationContext,
    BiometricObservationContext
)

# Load environment variables
load_dotenv()

async def test_observation_contexts():
    """Test creating and using observation contexts."""
    print("Testing observation contexts...")
    
    # Test sleep observation context
    print("\nTesting SleepObservationContext:")
    sleep_context = SleepObservationContext(agent_name="SleepAgent", user_id="test_user_1")
    
    # Test updating with data
    sleep_data = {
        "sleep_data": [
            {
                "date": "2023-01-01",
                "sleep_hours": 7.5,
                "deep_sleep": 1.2,
                "rem_sleep": 2.0,
                "light_sleep": 4.3
            }
        ]
    }
    sleep_context.update_from_data(sleep_data)
    print(f"Sleep context after update: {sleep_context.__dict__}")
    
    # Test calculating relevancy
    sleep_query = "How has my sleep quality been over the past week?"
    sleep_relevancy = sleep_context.calculate_relevancy(sleep_query)
    print(f"Sleep relevancy for '{sleep_query}': {sleep_relevancy}")
    
    # Test generating response
    sleep_response = sleep_context.generate_response()
    print(f"Sleep response: {sleep_response}")
    
    # Test exercise observation context
    print("\nTesting ExerciseObservationContext:")
    exercise_context = ExerciseObservationContext(agent_name="ExerciseAgent", user_id="test_user_1")
    
    # Test updating with data
    exercise_data = {
        "exercise_data": [
            {
                "date": "2023-01-01",
                "steps": 8000,
                "active_calories": 400,
                "workout_minutes": 45,
                "heart_rate": 140
            }
        ]
    }
    exercise_context.update_from_data(exercise_data)
    print(f"Exercise context after update: {exercise_context.__dict__}")
    
    # Test calculating relevancy
    exercise_query = "How many calories did I burn during my workouts this week?"
    exercise_relevancy = exercise_context.calculate_relevancy(exercise_query)
    print(f"Exercise relevancy for '{exercise_query}': {exercise_relevancy}")
    
    # Test generating response
    exercise_response = exercise_context.generate_response()
    print(f"Exercise response: {exercise_response}")
    
    # Test nutrition observation context
    print("\nTesting NutritionObservationContext:")
    nutrition_context = NutritionObservationContext(agent_name="NutritionAgent", user_id="test_user_1")
    
    # Test updating with data
    nutrition_data = {
        "nutrition_data": [
            {
                "date": "2023-01-01",
                "calories": 2000,
                "protein": 100,
                "carbs": 200,
                "fat": 70
            }
        ]
    }
    nutrition_context.update_from_data(nutrition_data)
    print(f"Nutrition context after update: {nutrition_context.__dict__}")
    
    # Test calculating relevancy
    nutrition_query = "What's my macronutrient breakdown for the past week?"
    nutrition_relevancy = nutrition_context.calculate_relevancy(nutrition_query)
    print(f"Nutrition relevancy for '{nutrition_query}': {nutrition_relevancy}")
    
    # Test generating response
    nutrition_response = nutrition_context.generate_response()
    print(f"Nutrition response: {nutrition_response}")
    
    # Test biometric observation context
    print("\nTesting BiometricObservationContext:")
    biometric_context = BiometricObservationContext(agent_name="BiometricAgent", user_id="test_user_1")
    
    # Test updating with data
    biometric_data = {
        "biometric_data": [
            {
                "date": "2023-01-01",
                "heart_rate": 70,
                "blood_pressure": "120/80",
                "weight": 70,
                "body_fat": 15
            }
        ]
    }
    biometric_context.update_from_data(biometric_data)
    print(f"Biometric context after update: {biometric_context.__dict__}")
    
    # Test calculating relevancy
    biometric_query = "What's my current heart rate variability?"
    biometric_relevancy = biometric_context.calculate_relevancy(biometric_query)
    print(f"Biometric relevancy for '{biometric_query}': {biometric_relevancy}")
    
    # Test generating response
    biometric_response = biometric_context.generate_response()
    print(f"Biometric response: {biometric_response}")

if __name__ == "__main__":
    asyncio.run(test_observation_contexts()) 