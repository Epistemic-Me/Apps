"""
AI Helper module for the Dialectic Test Harness.
Implements belief analysis and learning progress tracking.
"""

import os
from typing import Dict, Optional, Any
from openai import OpenAI
import json
import logging
import re

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
        self.model = "gpt-4o"  # Points to gpt-4o-2024-08-06
        
    def _clean_json_response(self, content: str) -> str:
        """Clean the JSON response by removing markdown code blocks."""
        # Remove markdown code block markers if present
        content = re.sub(r'^```json\s*', '', content)
        content = re.sub(r'\s*```$', '', content)
        return content.strip()
        
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
                
        Raises:
            ValueError: If the response cannot be parsed as valid JSON
            Exception: For other errors during analysis
        """
        # Prepare the system prompt
        system_prompt = self._create_analysis_prompt(learning_objective, belief_system)
        
        try:
            # Get analysis from OpenAI using new API format
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "Please provide the comprehensive analysis in valid JSON format."}
                ],
                temperature=0.2  # Lower temperature for more consistent analysis
            )
            
            # Get the response content and clean it
            content = self._clean_json_response(response.choices[0].message.content)
            
            try:
                # Parse the response
                analysis = json.loads(content)
            except json.JSONDecodeError as e:
                logging.error(f"Failed to parse JSON response: {content}")
                raise ValueError(f"OpenAI response was not valid JSON: {str(e)}")
            
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

    def analyze_beliefs(self, beliefs: list, learning_objective: dict) -> dict:
        """
        Analyze a list of beliefs against a learning objective.
        
        Args:
            beliefs: List of belief dictionaries with content, type, evidence, topic, and confidence
            learning_objective: Dictionary with description, topics, and required_aspects
        
        Returns:
            Dictionary containing analysis results
        """
        client = OpenAI(api_key=self.api_key)
        
        # Prepare the analysis prompt
        prompt = f"""Analyze the following beliefs against the learning objective:

Learning Objective: {learning_objective['description']}
Required Topics: {', '.join(learning_objective['topics'])}
Required Aspects: {', '.join(learning_objective['required_aspects'])}

Beliefs:
{json.dumps(beliefs, indent=2)}

Analyze these beliefs and provide:
1. Coverage and quality metrics for each topic
2. Key insights gained from each topic
3. Suggested areas for further exploration

Format the response as a JSON object with this structure:
{{
    "topic_coverage": {{
        "topic_name": {{
            "coverage": float,  // Percentage coverage (0-100)
            "quality": float,   // Quality score (0-10)
            "insights": [str],  // List of key insights
        }}
    }},
    "suggestions": [str]  // List of suggested focus areas
}}"""

        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert in analyzing learning progress and belief systems."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            # Parse the response
            analysis_text = response.choices[0].message.content
            # Extract JSON from the response (it might be wrapped in markdown code blocks)
            json_match = re.search(r'```json\n(.*)\n```', analysis_text, re.DOTALL)
            if json_match:
                analysis_text = json_match.group(1)
            
            analysis = json.loads(analysis_text)
            return analysis
            
        except Exception as e:
            logging.error(f"Error in belief analysis: {str(e)}")
            return {
                "topic_coverage": {},
                "suggestions": ["Error in analysis: " + str(e)]
            }

    def calculate_topic_coverage(self, beliefs, topics):
        """Calculate how well the beliefs cover the given topics."""
        covered_topics = set()
        for belief in beliefs:
            topic = belief.get("topic")
            if topic in topics:
                covered_topics.add(topic)
        return len(covered_topics) / len(topics) if topics else 0.0

    def assess_insight_quality(self, belief):
        """Assess the quality of insights in a belief."""
        content = belief.get("content", "").lower()
        
        # Check for specific quality indicators
        quality_indicators = {
            "specific_examples": bool(re.search(r"for (example|instance)|like when|such as", content)),
            "personal_experience": bool(re.search(r"i (found|noticed|realized|discovered|learned)", content)),
            "cause_effect": bool(re.search(r"because|therefore|as a result|this leads to|which means", content)),
            "reflection": bool(re.search(r"i think|in my experience|i believe|i feel|i've found", content))
        }
        
        # Calculate quality score (0.0 to 1.0)
        return sum(quality_indicators.values()) / len(quality_indicators)

    def assess_personal_relevance(self, belief):
        """Assess how personally relevant and applicable the belief is."""
        content = belief.get("content", "").lower()
        
        # Check for personal relevance indicators
        relevance_indicators = {
            "personal_pronouns": bool(re.search(r"\b(i|my|me|mine)\b", content)),
            "action_oriented": bool(re.search(r"\b(do|did|tried|started|implemented|practice)\b", content)),
            "specific_context": bool(re.search(r"when i|during|while|in the|at (work|home|gym)", content)),
            "impact_description": bool(re.search(r"helps|improved|noticed|felt|experienced", content))
        }
        
        # Calculate relevance score (0.0 to 1.0)
        return sum(relevance_indicators.values()) / len(relevance_indicators)