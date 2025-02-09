"""
Example script demonstrating the use of the belief analyzer for tracking learning progress.
This script tests the belief analysis functionality using simulated beliefs, without connecting to the server.

The script demonstrates:
1. How to structure learning objectives with specific topics and descriptions
2. How to format beliefs with content, type, and supporting evidence
3. How to interpret the analysis results including coverage, missing aspects, and suggested questions

Analysis Categories:
- Foundational: Basic understanding and principles
- Practice-based: Actual habits and routines
- Cause-effect: Understanding of impacts and relationships
- Experience-based: Personal observations and learnings

Quality Metrics:
- Clarity: How clearly the beliefs are expressed
- Evidence: Quality of supporting evidence
- Personal Context: Level of personal experience/application
"""

import os
import json
from dialectic_harness.ai_helper import BeliefAnalyzer

def run_learning_analysis(api_key: str):
    """
    Run a learning analysis example using simulated beliefs.
    
    The example shows a partial understanding across topics, with:
    - Mix of action-based and hypothesis-based evidence
    - Gaps in scientific understanding
    - Varying levels of certainty in beliefs
    - Interconnections between topics (e.g., stress affecting sleep)
    """
    # Define a more specific learning objective
    learning_objective = {
        "description": "Understanding the user's beliefs about sleep, diet, and exercise habits, including their personal experiences, scientific understanding, and how these factors interact",
        "topics": ["sleep", "diet", "exercise"],
        "completion_percentage": 0
    }
    
    # Define more nuanced simulated beliefs with some gaps
    simulated_beliefs = {
        "beliefs": [
            {
                "content": "I believe that 7-9 hours of sleep per night is important, but I often only get 6",
                "type": "STATEMENT",
                "evidence": {
                    "type": "ACTION",
                    "content": "I notice I'm less productive when I get less sleep"
                }
            },
            {
                "content": "I try to eat vegetables with dinner, though I'm not sure about proper portions",
                "type": "STATEMENT",
                "evidence": {
                    "type": "ACTION",
                    "content": "I feel better on days when I eat more vegetables"
                }
            },
            {
                "content": "Exercise helps my mood, especially in the morning",
                "type": "STATEMENT",
                "evidence": {
                    "type": "ACTION",
                    "content": "Morning workouts give me more energy throughout the day"
                }
            },
            {
                "content": "I believe stress affects my sleep quality, but I'm not sure how to manage it",
                "type": "STATEMENT",
                "evidence": {
                    "type": "HYPOTHESIS",
                    "content": "I tend to sleep worse when work is stressful"
                }
            },
            {
                "content": "I think meal timing matters for energy levels",
                "type": "STATEMENT",
                "evidence": {
                    "type": "HYPOTHESIS",
                    "content": "I feel sluggish after large lunches"
                }
            }
        ]
    }
    
    # Initialize the belief analyzer
    analyzer = BeliefAnalyzer(api_key=api_key)
    
    # Run the analysis
    analysis = analyzer.analyze_learning_progress(
        learning_objective=learning_objective,
        belief_system=simulated_beliefs
    )
    
    # Print the results
    print("\n=== Learning Progress Analysis ===")
    print(f"Overall Completion: {analysis['completion_percentage']}%")
    print("\nTopic Coverage:")
    for topic, coverage in analysis["topic_coverage"].items():
        print(f"\n{topic.title()}:")
        print(f"  Coverage: {coverage['percentage']}%")
        print("  Categories:")
        for category, score in coverage["categories"].items():
            print(f"    - {category}: {score*100:.1f}%")
        if coverage.get("missing_aspects"):
            print("  Missing Aspects:")
            for aspect in coverage["missing_aspects"]:
                print(f"    - {aspect}")
    
    print("\nQuality Metrics:")
    for metric, score in analysis["quality_metrics"].items():
        print(f"  - {metric}: {score*100:.1f}%")
    
    print("\nSuggested Questions:")
    for topic, coverage in analysis["topic_coverage"].items():
        if coverage.get("suggested_questions"):
            print(f"\n{topic.title()} Questions:")
            for question in coverage["suggested_questions"]:
                print(f"  - {question}")

if __name__ == "__main__":
    # Get API key from environment
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable must be set")
    
    # Run the example with just the OpenAI API key
    run_learning_analysis(api_key) 