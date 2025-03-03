"""
Chatbot evaluation using DeepEval.
"""

import os
import json
from dotenv import load_dotenv
from deepeval import evaluate
from deepeval.test_case import LLMTestCase
from deepeval.metrics import (
    AnswerRelevancyMetric,
    FaithfulnessMetric,
    TaskCompletionMetric,
)
from deepeval.synthesizer import Synthesizer

# Load environment variables
load_dotenv()

# Define test cases
def create_test_cases():
    """
    Create test cases for evaluation.
    
    This can either use predefined test cases or generate synthetic ones.
    """
    # Example of manually defined test cases
    test_cases = [
        # Test case for biomarker assessment
        LLMTestCase(
            input="My HbA1c is 5.9%, and my fasting glucose is 105 mg/dL. What does this mean for my biological age?",
            actual_output="Your HbA1c of 5.9% is slightly elevated, placing you in the prediabetic range (5.7-6.4%). Your fasting glucose of 105 mg/dL is also in the prediabetic range (100-125 mg/dL). These biomarkers suggest your glucose metabolism is contributing to accelerated biological aging. Research indicates that for each 1% increase in HbA1c above optimal levels of 5.0%, biological age may increase by 4-6 years. With your HbA1c at 5.9%, this suggests approximately 3.6-5.4 years of additional biological age compared to someone with optimal levels. Elevated fasting glucose contributes to this aging through processes like glycation and oxidative stress. These processes damage proteins and DNA, accelerating cellular aging. If you improve these biomarkers through lifestyle changes, you could potentially decrease your biological age by several years.",
            retrieval_context=[
                "HbA1c above 5.7% indicates pre-diabetes risk. Each 1% increase above optimal may add 4-6 years to biological age.",
                "Fasting glucose between 100-125 mg/dL indicates prediabetes. Levels above normal range accelerate aging through glycation and oxidative stress."
            ]
        ),
        
        # Test case for exercise recommendations
        LLMTestCase(
            input="I'd like to improve my biomarkers through exercise. What would you recommend?",
            actual_output="Based on your interest in exercise, I recommend implementing a progressive resistance training program 2-3 times per week, focusing on compound movements like squats, deadlifts, and push-ups. This type of training has been shown to improve insulin sensitivity and glucose metabolism, potentially helping address your elevated HbA1c and fasting glucose. Additionally, consider adding 20-30 minutes of zone 2 cardio (where you can still maintain a conversation) 2-3 times weekly to further enhance metabolic health. Start gradually and increase intensity over time. Would you like more specific guidance on getting started with a resistance training program?",
            retrieval_context=[
                "Resistance training improves insulin sensitivity and increases hormonal production, particularly testosterone.",
                "Regular strength training helps build and maintain muscle mass, which is essential for metabolic health.",
                "Start with 2-3 sessions per week of full-body resistance training. Focus on compound movements and gradually increase weight/resistance."
            ]
        ),
        
        # Test case for data completeness guidance
        LLMTestCase(
            input="What additional data should I collect to get a better picture of my biological age?",
            actual_output="Looking at your current health profile, I recommend collecting data in the following areas to get a more complete picture of your biological age:\n\n1. Bio Age Tests: Considering you already have some blood biomarkers, adding functional assessments would provide valuable complementary information. Grip strength is particularly useful and easy to measure - you can use a simple hand dynamometer available online for around $30. Push-up capacity is also valuable and requires no equipment.\n\n2. Lab Results: If you're willing to invest in more advanced testing, a DNA methylation test (like those from TruDiagnostic or MyDNAge) would provide the most accurate biological age assessment currently available.\n\n3. Health Data: Simply tracking your resting heart rate variability (HRV) using a wearable device can provide insights into your autonomic nervous system health, which correlates with biological age.\n\nCollecting these additional data points would increase your overall health profile completeness from 25% to approximately 60%, giving us a much more holistic view of your biological age status.",
            retrieval_context=[
                "Functional assessments like grip strength complement blood biomarkers for a more complete biological age assessment.",
                "DNA methylation patterns are currently the most accurate measure of biological age.",
                "Heart rate variability correlates with autonomic nervous system health and biological age."
            ],
            task="Suggest next most valuable measurements for assessing biological age"
        ),
        
        # Test case for integrating data from multiple categories
        LLMTestCase(
            input="I've added several measurements from different categories. Can you give me a holistic assessment of my biological age?",
            actual_output="Based on the comprehensive data you've provided across multiple categories, I can give you a holistic assessment of your biological age:\n\nYour blood biomarkers (particularly HbA1c, fasting glucose, and inflammation markers) suggest a metabolic age approximately 3-4 years above your chronological age. However, your functional assessments tell a different story - your grip strength and push-up capacity indicate a physiological age about 2 years below your chronological age, which is excellent.\n\nYour body composition measurements (particularly your waist-to-height ratio and body fat percentage) align closely with your chronological age.\n\nIntegrating all these measurements, your overall biological age appears to be approximately 1-2 years above your chronological age, primarily driven by your metabolic markers. The good news is that your functional fitness is already excellent, which research suggests can partially offset the effects of metabolic aging.\n\nThe most impactful area to focus on would be improving your glucose regulation through diet and continued exercise, as this would likely bring your biological age below your chronological age, given your already strong performance in physical capability tests.",
            retrieval_context=[
                "Biological age is best assessed through multiple measurement types including blood biomarkers, functional assessments, and body composition.",
                "Strong physical capabilities can partially offset poor metabolic biomarkers in determining overall biological age.",
                "Glucose regulation has a significant impact on overall biological aging processes."
            ],
            task="Provide a holistic assessment of biological age by integrating data from multiple categories"
        ),
        
        # Test case for explaining how data categories relate to biological age
        LLMTestCase(
            input="How do these different categories of health data relate to biological age?",
            actual_output="The different categories of health data each provide unique and complementary insights into biological aging:\n\n1. Biomarkers (blood/urine tests): These reveal your internal biochemistry, showing how well your metabolic, inflammatory, and hormonal systems are functioning. For example, HbA1c reflects glucose regulation over months, which directly impacts cellular aging through glycation.\n\n2. Bio Age Tests: These functional assessments measure how your body physically performs, reflecting the integrated output of multiple biological systems. Grip strength, for instance, correlates strongly with longevity because it indicates overall neuromuscular health and protein status.\n\n3. Capabilities: These broader functional measures assess how well your body's systems work together. VO2 max measures cardiorespiratory fitness, which reflects mitochondrial, pulmonary, cardiovascular, and muscular health simultaneously.\n\n4. Health Data: Daily metrics like sleep quality, activity levels, and heart rate variability show how your body responds to and recovers from stress, revealing autonomic nervous system health and resilience.\n\n5. Measurements: Physical measurements like waist-to-height ratio indicate fat distribution patterns, which correlate with metabolic health and inflammation levels.\n\n6. Lab Results: Advanced tests like epigenetic clocks and telomere length directly measure cellular aging processes, often providing the most accurate biological age assessments.\n\nIntegrating data across these categories provides the most comprehensive and accurate picture of biological age, as each category captures different aspects of the aging process. This is why collecting data from multiple categories leads to a more accurate and actionable biological age assessment.",
            retrieval_context=[
                "Different measurement types reflect distinct aspects of the aging process.",
                "Epigenetic clocks directly measure cellular aging mechanisms, while functional tests show the phenotypic expression of aging.",
                "Integrating multiple measurement types provides a more accurate and actionable biological age assessment than any single measurement."
            ],
            task="Explain how different categories of health data provide insights into biological age"
        )
    ]
    return test_cases

def generate_synthetic_test_cases(n=5):
    """
    Generate synthetic test cases using DeepEval's Synthesizer.
    """
    # Load biomarker and protocol data to inform the synthesizer
    try:
        with open("data/biomarkers.json", 'r') as f:
            biomarker_data = json.load(f)
        with open("data/protocols.json", 'r') as f:
            protocol_data = json.load(f)
    except Exception as e:
        print(f"Error loading data: {e}")
        return []
    
    # Create context from biomarker and protocol data
    context = []
    for category_key, category_data in biomarker_data.get("categories", {}).items():
        for item in category_data.get("items", []):
            context.append(f"{item['name']} ({category_data['display_name']}): {item['description']}. " +
                          f"Normal range: {item['normal_range']['min']}-{item['normal_range']['max']} " +
                          f"{item.get('unit', '')}. {item.get('age_impact', '')}")
    
    for protocol in protocol_data.get("protocols", []):
        context.append(f"{protocol['name']}: {protocol['description']}. Benefits: {', '.join(protocol['benefits'])}. Implementation: {protocol['implementation']}")
    
    # For now, let's fall back to predefined test cases since Synthesizer API has changed
    print("Using predefined test cases instead of synthetic ones due to Synthesizer API changes.")
    return create_test_cases()

def run_evaluation(use_synthetic=True, num_synthetic=5):
    """
    Run evaluation on test cases.
    """
    if use_synthetic:
        test_cases = generate_synthetic_test_cases(n=num_synthetic)
    else:
        test_cases = create_test_cases()
    
    # Define metrics
    metrics = [
        AnswerRelevancyMetric(threshold=0.7),
        # We could add more metrics like TaskCompletionMetric for the test cases that have tasks defined
    ]
    
    # Run evaluation
    results = evaluate(test_cases=test_cases, metrics=metrics)
    
    # Print results summary
    print("\n=== Evaluation Results Summary ===")
    print(f"Total test cases: {len(test_cases)}")
    
    # DeepEval API might have changed, so we'll use a more generic approach to summarize results
    print("\nResults have been printed above by DeepEval.")
    print("You can run 'deepeval login' to analyze results on Confident AI.")
    
    return results

if __name__ == "__main__":
    run_evaluation(use_synthetic=False) # Use our predefined test cases 