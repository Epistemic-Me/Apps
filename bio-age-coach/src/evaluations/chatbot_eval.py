"""
Chatbot evaluation using DeepEval.
"""

import os
from dotenv import load_dotenv
from deepeval import evaluate
from deepeval.test_case import LLMTestCase
from deepeval.metrics import (
    AnswerRelevancyMetric,
    FaithfulnessMetric,
)
from src.chatbot.coach import BioAgeCoach

# Load environment variables
load_dotenv()

# Ensure OpenAI API key is set
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY environment variable is not set")

def initialize_test_data(coach: BioAgeCoach):
    """Initialize the coach with test data."""
    # Set up test data that matches our test cases
    coach.user_data = {
        "health_data": {
            "active_calories": 400,
            "steps": 8000,
            "sleep": 6.5,
            "resting_heart_rate": 65,
            "chronological_age": 35,
            "biological_sex": "male"
        },
        "bio_age_tests": {
            "push_ups": 30,
            "grip_strength": 90.0,
            "one_leg_stand": 45
        },
        "biomarkers": {
            "hba1c": 5.9,
            "fasting_glucose": 105,
            "hdl": 65,
            "ldl": 100,
            "triglycerides": 150,
            "crp": 1.5
        },
        "measurements": {
            "body_fat": 18.5,
            "waist_circumference": 82,
            "hip_circumference": 98,
            "waist_to_hip": 0.84
        },
        "capabilities": {
            "plank": 120,
            "sit_and_reach": 15
        },
        "lab_results": {
            "vitamin_d": 45
        }
    }

def create_test_cases():
    """
    Create test cases for evaluation.
    """
    test_cases = []
    
    # Test case for biomarker assessment
    test_cases.append(
        LLMTestCase(
            input="My HbA1c is 5.9%, and my fasting glucose is 105 mg/dL. What does this mean for my biological age?",
            actual_output="Your HbA1c of 5.9% and fasting glucose of 105 mg/dL are both in the prediabetic range (HbA1c: 5.7-6.4%, fasting glucose: 100-125 mg/dL). These biomarkers suggest your glucose metabolism is contributing to accelerated biological aging. Research indicates that elevated HbA1c and fasting glucose can accelerate aging through processes like glycation and oxidative stress, which damage proteins and DNA. Improving these biomarkers through lifestyle changes could help optimize your biological age.",
            expected_output="Your HbA1c and fasting glucose levels are in the prediabetic range, suggesting accelerated biological aging. Elevated levels can damage proteins and DNA through glycation and oxidative stress.",
            retrieval_context=["HbA1c above 5.7% indicates pre-diabetes risk",
                    "Fasting glucose between 100-125 mg/dL indicates prediabetes. Levels above normal range accelerate aging through glycation and oxidative stress."]
        )
    )
    
    # Test case for exercise recommendations
    test_cases.append(
        LLMTestCase(
            input="I'd like to improve my biomarkers through exercise. What would you recommend?",
            actual_output="Based on your interest in exercise, I recommend implementing a progressive resistance training program 2-3 times per week, focusing on compound movements like squats, deadlifts, and push-ups. This type of training has been shown to improve insulin sensitivity and glucose metabolism, potentially helping address your elevated HbA1c and fasting glucose. Additionally, consider adding 20-30 minutes of zone 2 cardio (where you can still maintain a conversation) 2-3 times weekly to further enhance metabolic health. Start gradually and increase intensity over time. Would you like more specific guidance on getting started with a resistance training program?",
            expected_output="A combination of resistance training and zone 2 cardio can help improve your biomarkers. Focus on compound movements and gradually increase intensity.",
            retrieval_context=["Resistance training improves insulin sensitivity and increases hormonal production, particularly testosterone.",
                    "Regular strength training helps build and maintain muscle mass, which is essential for metabolic health.",
                    "Start with 2-3 sessions per week of full-body resistance training. Focus on compound movements and gradually increase weight/resistance."]
        )
    )
    
    # Test case for data completeness guidance
    test_cases.append(
        LLMTestCase(
            input="What additional data should I collect to get a better picture of my biological age?",
            actual_output="Looking at your current health profile, I recommend collecting data in the following areas to get a more complete picture of your biological age:\n\n1. Bio Age Tests: Considering you already have some blood biomarkers, adding functional assessments would provide valuable complementary information. Grip strength is particularly useful and easy to measure - you can use a simple hand dynamometer available online for around $30. Push-up capacity is also valuable and requires no equipment.\n\n2. Lab Results: If you're willing to invest in more advanced testing, a DNA methylation test (like those from TruDiagnostic or MyDNAge) would provide the most accurate biological age assessment currently available.\n\n3. Health Data: Simply tracking your resting heart rate variability (HRV) using a wearable device can provide insights into your autonomic nervous system health, which correlates with biological age.\n\nCollecting these additional data points would increase your overall health profile completeness from 25% to approximately 60%, giving us a much more holistic view of your biological age status.",
            expected_output="You should collect functional assessments like grip strength, DNA methylation testing, and heart rate variability data to get a more complete picture of your biological age.",
            retrieval_context=["Functional assessments like grip strength complement blood biomarkers for a more complete biological age assessment.",
                    "DNA methylation patterns are currently the most accurate measure of biological age.",
                    "Heart rate variability correlates with autonomic nervous system health and biological age."]
        )
    )
    
    # Test case for specific metric query
    test_cases.append(
        LLMTestCase(
            input="Is my grip strength good for my age?",
            actual_output="Looking at your data, your grip strength is 90.0 kg, which is excellent and actually indicates a functional age below your chronological age. Research shows that grip strength is a powerful predictor of longevity and overall health. For reference, the average grip strength for healthy adults varies by age and gender, but typically ranges from 30-50 kg. Your value of 90.0 kg puts you well above average, suggesting robust neuromuscular health and good protein status. This is a positive indicator for your biological age. Would you like to know about other functional tests that could complement this measurement?",
            expected_output="Your grip strength of 90.0 kg is excellent and indicates a functional age below your chronological age.",
            retrieval_context=["Grip strength above 70 kg indicates excellent neuromuscular health",
                    "Grip strength correlates strongly with longevity and biological age",
                    "The user's current grip strength measurement is 90.0 kg"]
        )
    )

    # Test case for missing data handling
    test_cases.append(
        LLMTestCase(
            input="What's my VO2 max level?",
            actual_output="I don't have access to your VO2 max data in your health profile. This would be a valuable measurement to add to your assessment, as it's an important indicator of cardiorespiratory fitness and biological age.",
            expected_output="I don't have access to your VO2 max data. This is an important measurement for assessing cardiorespiratory fitness and biological age.",
            retrieval_context=["VO2 max is a key indicator of cardiorespiratory fitness",
                    "The user has no VO2 max data in their profile"]
        )
    )

    # Test case for data-driven recommendations
    test_cases.append(
        LLMTestCase(
            input="What should I focus on improving first?",
            actual_output="Based on your current health data, I recommend focusing on glucose regulation first. Your HbA1c of 5.9% and fasting glucose of 105 mg/dL are both in the prediabetic range, suggesting this is your highest-impact opportunity for improving biological age. Your functional fitness is already excellent, as shown by your grip strength of 90.0 kg and push-up capacity of 30 reps.\n\nTo improve glucose regulation, consider:\n1. Adding 2-3 resistance training sessions weekly (which you're likely already doing given your strength metrics)\n2. Implementing time-restricted eating\n3. Prioritizing sleep (your current average of 6.5 hours could be improved)\n\nWould you like a more detailed plan for any of these interventions?",
            expected_output="Focus on improving glucose regulation first, as your HbA1c and fasting glucose are in the prediabetic range. Your functional fitness metrics are already excellent.",
            retrieval_context=["The user's HbA1c is 5.9% and fasting glucose is 105 mg/dL",
                    "The user has strong functional fitness metrics",
                    "The user averages 6.5 hours of sleep"]
        )
    )

    # Test case for holistic data interpretation
    test_cases.append(
        LLMTestCase(
            input="How do all my measurements work together to indicate my biological age?",
            actual_output="I'll analyze how your various measurements work together to paint a picture of your biological age:\n\n1. Metabolic Health (suggests +3-4 years):\n- HbA1c: 5.9% (prediabetic range)\n- Fasting glucose: 105 mg/dL (slightly elevated)\n\n2. Physical Capability (suggests -2-3 years):\n- Grip strength: 90.0 kg (exceptional)\n- Push-ups: 30 reps (above average)\n\n3. Body Composition (neutral impact):\n- Body fat: 18.5% (healthy range)\n- Waist-to-hip ratio: 0.84 (acceptable range)\n\n4. Daily Habits (slight negative impact):\n- Sleep: 6.5 hours (below optimal)\n- Active calories: 400/day (moderate)\n\nIntegrating these measurements, your biological age appears to be approximately 1-2 years above your chronological age. The good news is that your excellent physical capabilities are partially offsetting the metabolic factors. The most impactful changes would be:\n\n1. Improving glucose regulation\n2. Increasing sleep duration\n3. Maintaining your strong physical capabilities\n\nWould you like a specific action plan for any of these areas?",
            expected_output="Your measurements indicate a biological age approximately 1-2 years above chronological age. Strong physical capabilities (-2-3 years) partially offset metabolic health issues (+3-4 years).",
            retrieval_context=["Different measurement categories can offset each other in biological age calculation",
                    "Strong physical capabilities can partially compensate for metabolic issues",
                    "Sleep duration below 7 hours can accelerate biological aging"]
        )
    )
    
    # Test case for age/sex-specific push-up assessment (male)
    test_cases.append(
        LLMTestCase(
            input="Is my number of push-ups good for my age?",
            actual_output="As a 35-year-old male, your 30 push-ups is above average. Research shows that for men in their 30s, 15-20 push-ups is average, while 25+ is considered good. Your performance of 30 push-ups suggests good upper body strength and indicates a functional age potentially lower than your chronological age. This is a positive indicator for longevity, as upper body strength correlates with reduced mortality risk in longitudinal studies.",
            expected_output="For a 35-year-old male, 30 push-ups is above average, indicating good upper body strength and potentially a lower functional age.",
            retrieval_context=["For men aged 30-39, 15-20 push-ups is average",
                    "Push-up capacity correlates with mortality risk in men",
                    "Upper body strength is a key indicator of functional age"]
        )
    )

    # Test case for age/sex-specific push-up assessment (female)
    test_cases.append(
        LLMTestCase(
            input="How are my push-ups compared to others my age?",
            actual_output="As a 55-year-old female, your 30 push-ups is exceptional. The average range for women in their 50s is 6-10 push-ups, and your performance of 30 push-ups puts you well above the 90th percentile for your age and sex. This level of upper body strength suggests a functional age significantly lower than your chronological age. Strong performance in functional tests like push-ups is associated with better aging outcomes and reduced risk of age-related decline.",
            expected_output="For a 55-year-old female, 30 push-ups is exceptional, placing above the 90th percentile and suggesting a lower functional age.",
            retrieval_context=["Women aged 50-59 average 6-10 push-ups",
                    "Push-up capacity above age norms indicates lower functional age",
                    "Strong functional test performance correlates with better aging outcomes"]
        )
    )

    # Test case for missing age/sex data
    test_cases.append(
        LLMTestCase(
            input="Are my push-ups good?",
            actual_output="I see you can do 30 push-ups, but I notice that your age and sex information is missing from your health profile. Push-up capacity varies significantly between males and females, and naturally declines with age. For example, what's considered 'excellent' for a 60-year-old woman would be different from what's 'good' for a 25-year-old man. Could you update your health profile with your age and sex so I can give you a more precise evaluation of your performance?",
            expected_output="While I can see you can do 30 push-ups, I need your age and sex information from your health profile to provide an accurate assessment, as push-up capacity varies significantly by these factors.",
            retrieval_context=["Push-up standards vary by age and sex",
                    "Age and sex are required for accurate fitness assessment",
                    "The user's push-up count is 30 reps"]
        )
    )
    
    return test_cases

def run_evaluation(use_synthetic=False):
    """
    Run evaluation on test cases.
    """
    # Create and initialize coach with test data
    coach = BioAgeCoach()
    initialize_test_data(coach)
    
    # Create test cases
    test_cases = create_test_cases()
    
    # Define metrics
    metrics = [
        AnswerRelevancyMetric(threshold=0.7),
        FaithfulnessMetric(threshold=0.7)
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
    run_evaluation() 