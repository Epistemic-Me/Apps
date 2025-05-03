"""
Comprehensive biological age assessment evaluation suite.
"""

from typing import List, Dict, Any
from deepeval.test_case import LLMTestCase
from evaluations.framework import EvaluationSuite, RouterContext
from bio_age_coach.types import DataCategory

class ComprehensiveEvaluation(EvaluationSuite):
    """Evaluation suite for comprehensive biological age assessments."""
    
    async def setup(self):
        """Setup test environment with comprehensive data."""
        test_data = {
            DataCategory.HEALTH_METRICS.value: {
                "demographics": {
                    "age": 18,
                    "sex": "male"
                },
                "active_calories": 400,
                "steps": 8000,
                "sleep_hours": 6.5,
                "resting_heart_rate": 65
            },
            DataCategory.FITNESS_METRICS.value: {
                "capabilities": {
                    "push_ups": 30,
                    "grip_strength": 90,
                    "vo2_max": 45
                }
            },
            DataCategory.BIOMARKERS.value: {
                "hba1c": 5.9,
                "fasting_glucose": 105,
                "crp": 1.2,
                "vitamin_d": 45,
                "testosterone": 600
            },
            DataCategory.MEASUREMENTS.value: {
                "blood_pressure_systolic": 120,
                "blood_pressure_diastolic": 80,
                "body_fat": 18.5,
                "waist_circumference": 82.0
            }
        }
        
        # Initialize all servers with relevant data
        if self.context.health_server:
            await self.context.health_server.initialize_data(test_data)
        if self.context.tools_server:
            await self.context.tools_server.initialize_data(test_data)
        
        await super().setup()
        
        # Update coach's user data with all metrics
        self.coach.user_data.update({
            "health_data": test_data[DataCategory.HEALTH_METRICS.value],
            "capabilities": test_data[DataCategory.FITNESS_METRICS.value]["capabilities"],
            "biomarkers": test_data[DataCategory.BIOMARKERS.value],
            "measurements": test_data[DataCategory.MEASUREMENTS.value],
            "age": test_data[DataCategory.HEALTH_METRICS.value]["demographics"]["age"],
            "sex": test_data[DataCategory.HEALTH_METRICS.value]["demographics"]["sex"]
        })
    
    def create_test_cases(self) -> List[LLMTestCase]:
        """Create comprehensive assessment test cases."""
        return [
            self.create_test_case(
                input="What additional data should I collect to get a better picture of my biological age?",
                expected_output="You should collect functional assessments like grip strength, DNA methylation testing, and heart rate variability data to get a more complete picture of your biological age.",
                retrieval_context=[
                    "Functional assessments like grip strength complement blood biomarkers for a more complete biological age assessment",
                    "DNA methylation patterns are currently the most accurate measure of biological age",
                    "Heart rate variability correlates with autonomic nervous system health and biological age"
                ]
            ),
            self.create_test_case(
                input="What should I focus on improving first?",
                expected_output="Focus on improving glucose regulation first, as your HbA1c and fasting glucose are in the prediabetic range. Your functional fitness metrics are already excellent.",
                retrieval_context=[
                    "The user's HbA1c is 5.9% and fasting glucose is 105 mg/dL",
                    "The user has strong functional fitness metrics",
                    "The user averages 6.5 hours of sleep"
                ]
            ),
            self.create_test_case(
                input="How do all my measurements work together to indicate my biological age?",
                expected_output="Your measurements indicate a biological age approximately 1-2 years above chronological age. Strong physical capabilities (-2-3 years) partially offset metabolic health issues (+3-4 years).",
                retrieval_context=[
                    "Different measurement categories can offset each other in biological age calculation",
                    "Strong physical capabilities can partially compensate for metabolic issues",
                    "Sleep duration below 7 hours can accelerate biological aging"
                ]
            )
        ] 