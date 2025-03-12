"""
Health metrics evaluation suite.
"""

from typing import List, Dict, Any
from deepeval.test_case import LLMTestCase
from evaluations.framework import EvaluationSuite, RouterContext
from bio_age_coach.types import DataCategory

class HealthMetricsEvaluation(EvaluationSuite):
    """Evaluation suite for health metrics queries."""
    
    async def setup(self):
        """Setup test environment with health metrics data."""
        test_data = {
            DataCategory.HEALTH_METRICS.value: {
                "demographics": {
                    "age": 18,
                    "sex": "male"
                },
                "active_calories": 450,
                "steps": 8000,
                "heart_rate": 65,
                "sleep_hours": 7.5,
                "blood_pressure_systolic": 120,
                "blood_pressure_diastolic": 80,
                "resting_heart_rate": 65,
                "daily_metrics": {
                    "steps": [
                        {"startDate": "2024-03-01", "value": 8000},
                        {"startDate": "2024-03-02", "value": 8100},
                        {"startDate": "2024-03-03", "value": 8200}
                    ],
                    "active_calories": [
                        {"startDate": "2024-03-01", "value": 450},
                        {"startDate": "2024-03-02", "value": 450},
                        {"startDate": "2024-03-03", "value": 450}
                    ],
                    "heart_rate": [
                        {"startDate": "2024-03-01", "value": 65},
                        {"startDate": "2024-03-02", "value": 66},
                        {"startDate": "2024-03-03", "value": 65}
                    ]
                }
            }
        }
        
        if self.context.health_server:
            await self.context.health_server.initialize_data(test_data)
        
        await super().setup()
        
        self.coach.user_data.update({
            "health_data": test_data[DataCategory.HEALTH_METRICS.value],
            "age": test_data[DataCategory.HEALTH_METRICS.value]["demographics"]["age"],
            "sex": test_data[DataCategory.HEALTH_METRICS.value]["demographics"]["sex"]
        })
    
    def create_test_cases(self) -> List[LLMTestCase]:
        """Create health metrics-specific test cases."""
        return [
            LLMTestCase(
                input="How is my sleep affecting my biological age?",
                actual_output="Your sleep duration of 7.5 hours per night is adequate but slightly below optimal for your age group (18-25 years). While this provides basic recovery, increasing sleep to 8-10 hours could better support your biological age through improved hormone production and cognitive development.",
                expected_output="Your average sleep duration of 7.5 hours is within the healthy range but slightly below optimal for your age group (18-25 years: 8-10 hours recommended). While adequate for basic recovery, increasing sleep duration could further support growth hormone production, cognitive development, and optimal biological aging.",
                retrieval_context=[
                    "Sleep recommendations for ages 18-25: 8-10 hours per night",
                    "Sleep quality impacts hormone production and recovery",
                    "Consistent sleep patterns support optimal biological aging",
                    "User data: age=18, sex=male, sleep_hours=7.5"
                ]
            ),
            LLMTestCase(
                input="What do my activity levels indicate about my health?",
                actual_output="Your daily activity shows consistent engagement with 8,000 steps and 450 active calories burned. This meets recommended activity levels (7,000-10,000 steps/day) and indicates an active lifestyle supporting healthy cardiovascular function and metabolic health.",
                expected_output="Your daily activity profile shows consistent engagement with 8,000 steps and 450 active calories burned daily. This meets basic activity recommendations (7,000-10,000 steps/day) and suggests an active lifestyle. Your activity level is supporting healthy cardiovascular function and metabolic health, positively influencing your biological age markers.",
                retrieval_context=[
                    "Recommended daily steps: 7,000-10,000 steps",
                    "Active calorie burn >400 indicates good activity level",
                    "Consistent activity supports cardiovascular health",
                    "User data: age=18, sex=male, steps=8000, active_calories=450"
                ]
            ),
            LLMTestCase(
                input="Are my heart rate and blood pressure in healthy ranges?",
                actual_output="Your cardiovascular metrics are in optimal ranges with a resting heart rate of 65 bpm (60-70 bpm is ideal) and blood pressure of 120/80 mmHg. These values suggest healthy cardiovascular aging and efficient heart function.",
                expected_output="Your cardiovascular metrics are optimal: resting heart rate of 65 bpm indicates good cardiovascular fitness (60-70 bpm is ideal), and blood pressure of 120/80 mmHg is perfectly normal. These values suggest healthy cardiovascular aging and efficient heart function.",
                retrieval_context=[
                    "Optimal resting heart rate range: 60-70 bpm",
                    "Normal blood pressure: systolic <120, diastolic <80",
                    "Lower resting heart rate correlates with cardiovascular fitness",
                    "User data: age=18, sex=male, resting_heart_rate=65, blood_pressure_systolic=120, blood_pressure_diastolic=80"
                ]
            )
        ] 