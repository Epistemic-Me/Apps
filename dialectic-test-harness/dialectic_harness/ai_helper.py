"""
AI Helper module for the Dialectic Test Harness.
Implements belief analysis and learning progress tracking.
"""

import os
from typing import Dict, List, Optional, Any
from openai import OpenAI
import json
import logging

class BeliefAnalyzer:
    """
    Analyzes beliefs and learning progress using LLM-based analysis.
    Combines quality assessment and coverage analysis for comprehensive learning evaluation.
    """
    
    # Template for the expected JSON structure in the analysis
    ANALYSIS_TEMPLATE = """{
    "completion_percentage": float,  // Overall completion (0-100)
    "topic_coverage": {
        "topic_name": {
            "percentage": float,  // Topic completion (0-100)
            "categories": {
                "foundational": float,  // Category scores (0-1)
                "practice_based": float,
                "cause_effect": float,
                "experience_based": float
            },
            "missing_aspects": [str],  // List of missing aspects
            "suggested_questions": [str]  // Questions to fill gaps
        }
    },
    "quality_metrics": {
        "clarity": float,  // Overall clarity (0-1)
        "evidence": float,  // Evidence quality (0-1)
        "personal_context": float  // Personal context (0-1)
    }
}"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the BeliefAnalyzer.
        
        Args:
            api_key: OpenAI API key. If not provided, will try to get from OPENAI_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key must be provided or set in OPENAI_API_KEY env var")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = "gpt-4"  # Can be made configurable
        
    def analyze_learning_progress(self, 
                                learning_objective: Dict[str, Any], 
                                belief_system: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive analysis of learning progress combining quality and coverage analysis.
        
        Args:
            learning_objective: Dictionary containing:
                - description: str
                - topics: List[str]
                - completion_percentage: float
            belief_system: Dictionary containing:
                - beliefs: List[Dict] where each belief has:
                    - content: str
                    - type: str
                    - evidence: Optional[Dict]
                    
        Returns:
            Dictionary containing:
                - completion_percentage: float
                - topic_coverage: Dict[str, Dict] for each topic
                - quality_metrics: Dict[str, float]
                - suggested_questions: List[str]
        """
        # Prepare the system prompt
        system_prompt = self._create_analysis_prompt(learning_objective, belief_system)
        
        try:
            # Get analysis from OpenAI using new API format
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "Please provide the comprehensive analysis."}
                ],
                temperature=0.2  # Lower temperature for more consistent analysis
            )
            
            # Parse the response
            analysis = json.loads(response.choices[0].message.content)
            
            # Validate and clean the analysis
            return self._validate_analysis(analysis)
            
        except Exception as e:
            logging.error(f"Error in belief analysis: {str(e)}")
            raise
            
    def _create_analysis_prompt(self, 
                              learning_objective: Dict[str, Any], 
                              belief_system: Dict[str, Any]) -> str:
        """Creates the system prompt for the analysis."""
        return f"""Analyze the learning progress based on the following learning objective and belief system.

Learning Objective:
{json.dumps(learning_objective, indent=2)}

Current Beliefs:
{json.dumps(belief_system, indent=2)}

Analyze the beliefs in these categories:
1. Foundational Beliefs (25%)
   - Basic understanding of each topic
   - Core principles and values
2. Practice-Based Beliefs (25%)
   - Specific habits and routines
   - Personal methods and approaches
3. Cause-Effect Beliefs (25%)
   - Understanding of impacts and consequences
   - Connections between actions and results
4. Experience-Based Beliefs (25%)
   - Personal experiences and observations
   - Learned insights and adaptations

For each category, evaluate:
- Clear statement of belief (40%)
- Supporting details or examples (30%)
- Personal context or reasoning (30%)

Return a JSON object with EXACTLY this structure:
{self.ANALYSIS_TEMPLATE}"""

    def _validate_analysis(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Validates and cleans the analysis output."""
        required_keys = {
            "completion_percentage", 
            "topic_coverage", 
            "quality_metrics"
        }
        
        if not all(key in analysis for key in required_keys):
            raise ValueError(f"Analysis missing required keys: {required_keys}")
            
        # Ensure completion percentage is between 0-100
        analysis["completion_percentage"] = max(0, min(100, analysis["completion_percentage"]))
        
        # Validate topic coverage
        for topic, coverage in analysis["topic_coverage"].items():
            coverage["percentage"] = max(0, min(100, coverage["percentage"]))
            for category, score in coverage["categories"].items():
                coverage["categories"][category] = max(0, min(1, score))
                
        # Validate quality metrics
        for metric, score in analysis["quality_metrics"].items():
            analysis["quality_metrics"][metric] = max(0, min(1, score))
            
        return analysis 