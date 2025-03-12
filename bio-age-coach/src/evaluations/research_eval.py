"""
Research integration evaluation suite.
"""

from typing import List, Dict, Any
from deepeval.test_case import LLMTestCase
from evaluations.framework import EvaluationSuite, RouterContext
from bio_age_coach.types import DataCategory

class ResearchEvaluation(EvaluationSuite):
    """Evaluation suite for research-related queries."""
    
    async def setup(self):
        """Setup test environment with research data."""
        test_data = {
            "papers": [
                {
                    "title": "Grip Strength and Mortality",
                    "findings": [
                        "Strong correlation between grip strength and overall mortality",
                        "Grip strength is a reliable predictor of functional capacity",
                        "Age-specific grip strength standards provide context for assessment"
                    ]
                },
                {
                    "title": "Sleep Duration and Biological Aging",
                    "findings": [
                        "Sleep duration affects telomere length",
                        "Optimal sleep (7-9 hours) correlates with slower biological aging",
                        "Poor sleep quality accelerates cellular aging markers"
                    ]
                },
                {
                    "title": "HbA1c as Aging Biomarker",
                    "findings": [
                        "HbA1c strongly correlates with biological age acceleration",
                        "Glycation end-products accumulate with aging",
                        "Maintaining HbA1c below 5.7% optimal for longevity"
                    ]
                }
            ]
        }
        
        if self.context.research_server:
            await self.context.research_server.initialize_data(test_data)
        
        await super().setup()
    
    def create_test_cases(self) -> List[LLMTestCase]:
        """Create research-specific test cases."""
        return [
            LLMTestCase(
                input="What's the latest research on grip strength and longevity?",
                actual_output="According to recent research, grip strength has emerged as a significant predictor of longevity and overall health outcomes. Studies have found a strong correlation between grip strength and mortality rates, with grip strength serving as a reliable indicator of functional capacity. Research emphasizes the importance of using age-specific grip strength standards for accurate assessment, as these provide crucial context for evaluating an individual's health status and potential longevity.",
                expected_output="Recent research shows that grip strength is a powerful predictor of overall mortality and functional capacity. Studies have established strong correlations between grip strength and longevity, with age-specific standards providing important context for assessment. Higher grip strength is associated with better health outcomes and can be used as a reliable biomarker of biological age.",
                retrieval_context=[
                    "Strong correlation between grip strength and overall mortality",
                    "Grip strength is a reliable predictor of functional capacity",
                    "Age-specific grip strength standards provide context for assessment"
                ]
            ),
            LLMTestCase(
                input="How does sleep affect biological aging according to research?",
                actual_output="Research findings demonstrate that sleep plays a crucial role in biological aging processes. Studies have shown that sleep duration has a direct impact on telomere length, a key marker of cellular aging. The research indicates that maintaining optimal sleep duration of 7-9 hours is associated with slower biological aging. Additionally, poor sleep quality has been linked to accelerated cellular aging markers, suggesting that both the quantity and quality of sleep are important factors in managing biological age.",
                expected_output="Research indicates that sleep duration has a direct impact on biological aging markers, particularly telomere length. Studies show that optimal sleep duration of 7-9 hours correlates with slower biological aging processes. Poor sleep quality has been found to accelerate cellular aging markers, highlighting the importance of both sleep quantity and quality in managing biological age.",
                retrieval_context=[
                    "Sleep duration affects telomere length",
                    "Optimal sleep (7-9 hours) correlates with slower biological aging",
                    "Poor sleep quality accelerates cellular aging markers"
                ]
            ),
            LLMTestCase(
                input="What does research say about HbA1c and aging?",
                actual_output="Current research has established a strong connection between HbA1c levels and biological aging. Studies show that HbA1c is a significant indicator of biological age acceleration, with higher levels associated with faster aging. This is partly due to the accumulation of glycation end-products, which naturally increase with age but can accelerate the aging process when elevated. Research suggests that maintaining HbA1c below 5.7% is optimal for longevity and may help slow biological aging.",
                expected_output="Research demonstrates that HbA1c levels strongly correlate with biological age acceleration. Studies show that glycation end-products, measured by HbA1c, accumulate with aging and can accelerate the aging process. Maintaining HbA1c below 5.7% has been found optimal for longevity, as higher levels may contribute to accelerated biological aging.",
                retrieval_context=[
                    "HbA1c strongly correlates with biological age acceleration",
                    "Glycation end-products accumulate with aging",
                    "Maintaining HbA1c below 5.7% optimal for longevity"
                ]
            )
        ] 