"""
Biomarker evaluation suite.
"""

from typing import List, Dict, Any
from deepeval.test_case import LLMTestCase
from evaluations.framework import EvaluationSuite, RouterContext
from bio_age_coach.types import DataCategory

class BiomarkerEvaluation(EvaluationSuite):
    """Evaluation suite for biomarker queries."""
    
    async def setup(self):
        """Setup test environment with biomarker data."""
        test_data = {
            DataCategory.BIOMARKERS.value: {
                "hba1c": 5.9,
                "fasting_glucose": 105,
                "crp": 1.2,
                "vitamin_d": 45,
                "testosterone": 600,
                "cortisol": 15
            },
            DataCategory.HEALTH_METRICS.value: {
                "demographics": {
                    "age": 18,
                    "sex": "male"
                }
            }
        }
        
        if self.context.health_server:
            await self.context.health_server.initialize_data(test_data)
        
        await super().setup()
        
        self.coach.user_data.update({
            "biomarkers": test_data[DataCategory.BIOMARKERS.value],
            "age": test_data[DataCategory.HEALTH_METRICS.value]["demographics"]["age"],
            "sex": test_data[DataCategory.HEALTH_METRICS.value]["demographics"]["sex"]
        })
    
    def create_test_cases(self) -> List[LLMTestCase]:
        """Create biomarker-specific test cases."""
        return [
            self.create_test_case(
                input="My HbA1c is 5.9%, and my fasting glucose is 105 mg/dL. What does this mean for my biological age?",
                expected_output="Your HbA1c and fasting glucose levels are in the prediabetic range, suggesting accelerated biological aging. Elevated levels can damage proteins and DNA through glycation and oxidative stress.",
                retrieval_context=[
                    "HbA1c above 5.7% indicates pre-diabetes risk",
                    "Fasting glucose between 100-125 mg/dL indicates prediabetes",
                    "Levels above normal range accelerate aging through glycation and oxidative stress"
                ]
            ),
            self.create_test_case(
                input="I'd like to improve my biomarkers through exercise. What would you recommend?",
                expected_output="A combination of resistance training and zone 2 cardio can help improve your biomarkers. Focus on compound movements and gradually increase intensity.",
                retrieval_context=[
                    "Resistance training improves insulin sensitivity and increases hormonal production, particularly testosterone",
                    "Regular strength training helps build and maintain muscle mass, which is essential for metabolic health",
                    "Start with 2-3 sessions per week of full-body resistance training. Focus on compound movements and gradually increase weight/resistance"
                ]
            )
        ] 