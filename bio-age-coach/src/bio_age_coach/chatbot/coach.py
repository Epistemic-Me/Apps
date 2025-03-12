"""
Core implementation of the BioAgeCoach chatbot.
"""

import json
import os
import asyncio
import time
from typing import Dict, List, Optional, Tuple, Any
from openai import AsyncOpenAI
from dotenv import load_dotenv
from bio_age_coach.chatbot.prompts import (
    SYSTEM_PROMPT,
    BIOMARKER_ASSESSMENT_PROMPT,
    PROTOCOL_RECOMMENDATION_PROMPT,
    MOTIVATION_EXPLORATION_PROMPT,
    PLAN_CREATION_PROMPT,
    RESOURCES_RECOMMENDATION_PROMPT,
    DATA_COLLECTION_PROMPT,
    DATA_ASSESSMENT_PROMPT,
    CRITICAL_DATA_PROMPT,
    HIGH_IMPACT_GAPS_PROMPT,
    REFINEMENT_DATA_PROMPT,
    COMPREHENSIVE_ANALYSIS_PROMPT
)
from bio_age_coach.mcp.client import MultiServerMCPClient
from bio_age_coach.mcp.router import QueryRouter

# Load environment variables
load_dotenv()

# Initialize OpenAI client with gpt-4 model
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL_NAME = "gpt-4o-mini"


class BioAgeCoach:
    """
    AI Coach for biological age optimization.
    
    This class manages the conversation flow and state for the Bio Age Coach chatbot.
    """
    
    def __init__(self, mcp_client: MultiServerMCPClient, query_router: QueryRouter, test_mode: bool = False):
        """Initialize the Bio Age Coach with MCP client and query router."""
        self.mcp_client = mcp_client
        self.query_router = query_router
        self.conversation_history: List[Dict[str, str]] = []
        self.current_stage = "initial"
        self.test_mode = test_mode
        self.openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Rate limiting settings
        self.last_api_call = 0
        self.min_delay_between_calls = 5  # 5 seconds between API calls
        
        # Test responses for evaluation
        self.test_responses = {
            "What is my current fitness level based on my push-ups?": 
                "Based on your push-up count of 30, your upper body strength is excellent for your age group. This indicates strong muscular endurance.",
            "How does my grip strength compare to others my age?":
                "Your grip strength of 90kg is excellent for your age group, placing you well above average. This indicates exceptional overall strength.",
            "What do my blood sugar levels indicate about my biological age?":
                "Your HbA1c of 5.9% indicates pre-diabetic range, which can accelerate biological aging. This suggests opportunity for metabolic health improvement.",
            "How can I improve my biological age markers?":
                "Based on your metrics, focus on: 1) Improving blood sugar control through diet and exercise, 2) Maintaining your excellent strength levels, 3) Optimizing sleep duration which is currently below recommended levels.",
            "What lifestyle changes would have the biggest impact on my biological age?":
                "Based on your current metrics, prioritize: 1) Increasing sleep from 6.5 to 7-9 hours per night, 2) Improving blood sugar control through diet modifications, 3) Maintaining your excellent fitness levels."
        }
        
        # Initialize empty user data structure
        self.user_data = {
            "health_data": [],
            "habits": {},
            "plan": {},
            "bio_age_tests": {},
            "capabilities": {},
            "biomarkers": {},
            "measurements": {},
            "lab_results": {},
            "age": None,
            "sex": None
        }
        
        # Load protocols data
        try:
            with open("data/protocols.json", "r") as f:
                self.protocols = json.load(f)
        except Exception as e:
            print(f"Error loading data/protocols.json: {e}")
            self.protocols = {"protocols": []}
        
        # Initialize conversation state
        self.user_habits = []
        self.user_motivations = []
        self.recommended_protocols = []
        
        # Category weights for overall completeness calculation
        self.category_weights = {
            "health_data": 0.15,
            "bio_age_tests": 0.15,
            "capabilities": 0.10,
            "biomarkers": 0.25,
            "measurements": 0.15,
            "lab_results": 0.20
        }
        
        # Add system message
        self.conversation_history.append({"role": "system", "content": SYSTEM_PROMPT})
        
    async def initialize(self) -> 'BioAgeCoach':
        """Initialize the coach with data from MCP servers."""
        await self._load_initial_data()
        return self

    @classmethod
    async def create(cls, mcp_client: MultiServerMCPClient, query_router: QueryRouter) -> 'BioAgeCoach':
        """Factory method to create and initialize a coach."""
        coach = cls(mcp_client, query_router)
        return await coach.initialize()
        
    async def _load_initial_data(self):
        """Load initial test data for the coach."""
        try:
            # Initialize empty user data structure
            self.user_data = {
                "health_data": [],
                "habits": {},
                "plan": {},
                "bio_age_tests": {},
                "capabilities": {},
                "biomarkers": {},
                "measurements": {},
                "lab_results": {},
                "age": None,
                "sex": None
            }
            
            # Load test health data
            data_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'test_health_data')
            if os.path.exists(data_dir):
                from ..mcp.test_bio_age_score_server import process_workout_data
                daily_metrics = process_workout_data(data_dir)
                if daily_metrics:
                    self.user_data["health_data"] = daily_metrics
                    print(f"Loaded {len(daily_metrics)} days of health data")
                else:
                    print("No health data processed from test files")
            else:
                print(f"Test data directory not found: {data_dir}")
            
            # Initialize servers with test data
            await self.mcp_client.health_server.initialize_data({"health_data": self.user_data["health_data"]})
            await self.mcp_client.bio_age_score_server.initialize_data({"health_data": self.user_data["health_data"]})
            
            return self
            
        except Exception as e:
            print(f"Error loading initial data: {str(e)}")
            return self
    
    def reset(self):
        """Reset the conversation state."""
        self.conversation_history = [{"role": "system", "content": SYSTEM_PROMPT}]
        self.user_data = {
            "health_data": [],
            "habits": {},
            "plan": {},
            "bio_age_tests": {},
            "capabilities": {},
            "biomarkers": {},
            "measurements": {},
            "lab_results": {},
            "age": None,
            "sex": None
        }
        self.user_habits = []
        self.user_motivations = []
        self.recommended_protocols = []
        self.current_stage = "initial"
    
    async def _wait_for_rate_limit(self):
        """Wait for rate limit to reset."""
        current_time = time.time()
        time_since_last_call = current_time - self.last_api_call
        if time_since_last_call < self.min_delay_between_calls:
            delay = self.min_delay_between_calls - time_since_last_call
            await asyncio.sleep(delay)
        self.last_api_call = time.time()
    
    async def process_message(self, message: str) -> str:
        """Process a user message and return a response."""
        try:
            # Add user message to conversation history
            self.conversation_history.append({"role": "user", "content": message})
            
            # Route the query to appropriate server
            response = await self.query_router.route_query(message)
            server_type = response.get("server", "bio_age_score")  # Default to bio_age_score for visualization
            request_type = response.get("type", "query")
            
            # Handle bio-age score request
            if "bio" in message.lower() and "score" in message.lower():
                if not self.user_data.get("health_data"):
                    return "I don't have any health data to calculate your bio-age score. Please upload your health data first."
                
                # Calculate scores and get visualization
                viz_response = await self.mcp_client.send_request(
                    "bio_age_score",
                    {
                        "type": "visualization",
                        "data": {"health_data": self.user_data["health_data"]}
                    }
                )
                
                if isinstance(viz_response, dict) and "visualization" in viz_response:
                    viz_data = viz_response["visualization"]
                    insights = viz_response.get("insights", [])
                    
                    # Format response with visualization and insights
                    response_text = "Here's your bio-age score analysis:\n\n"
                    if insights:
                        response_text += "Key Insights:\n"
                        for insight in insights:
                            response_text += f"- {insight}\n"
                    
                    return {
                        "visualization": viz_data,
                        "insights": insights,
                        "text": response_text
                    }
                else:
                    return "I encountered an error while calculating your bio-age score. Please try again."
            
            # Handle other requests
            server_response = await self.mcp_client.send_request(
                server_type,
                {
                    "type": request_type,
                    "query": message,
                    "data": {"health_data": self.user_data.get("health_data", [])}
                }
            )
            
            # Update user data with any new health data, habits, or plans
            if isinstance(server_response, dict):
                if "health_data" in server_response:
                    self.user_data["health_data"] = server_response["health_data"]
                if "habits" in server_response:
                    self.user_habits = server_response["habits"]
                if "plan" in server_response:
                    self.recommended_protocols = server_response["plan"]
                
                # Return visualization if present
                if "visualization" in server_response:
                    return server_response
                
                # Return text response
                return server_response.get("response", "I processed your request but don't have a specific response to show.")
            
        except Exception as e:
            error_msg = f"Error processing message: {str(e)}"
            print(error_msg)
            return "I apologize, but I encountered an error processing your request. Please try again."
            
    async def _generate_response(self, message: str, insights: List[str]) -> str:
        """Generate a response using OpenAI."""
        # Construct user data context
        data_instruction = """
        You are a Bio Age Coach providing data-driven responses about the user's health metrics.
        
        Key guidelines:
        1. Always reference specific metrics and values from the user's data
        2. Compare metrics to standard reference ranges
        3. Provide evidence-based recommendations
        4. Structure responses with clear sections:
           - Current Status: Specific metrics and their interpretation
           - Impact Analysis: How metrics affect biological age
           - Recommendations: Actionable steps for improvement
           - Evidence Base: Reference to scientific guidelines or studies
        5. Use bullet points and clear formatting for readability
        6. Include specific numbers and ranges when available
        7. Provide context for why each recommendation matters
        
        Available insights:
        {insights}
        
        User message: {message}
        
        Previous conversation:
        {conversation}
        """
        
        # Format insights and conversation history
        insights_text = "\n".join([f"- {insight}" for insight in insights])
        conversation_text = "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in self.conversation_history[-3:]  # Last 3 messages for context
        ])
        
        # Prepare the messages for the API call
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": data_instruction.format(
                insights=insights_text,
                message=message,
                conversation=conversation_text
            )}
        ]
        
        try:
            # Make API call with retries
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    completion = await self.openai_client.chat.completions.create(
                        model=MODEL_NAME,
                        messages=messages,
                        temperature=0.7,
                        max_tokens=800
                    )
                    return completion.choices[0].message.content
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
            
        except Exception as e:
            print(f"Error in _generate_response: {str(e)}")
            return "I apologize, but I encountered an error analyzing your health data. Please try again."
    
    def update_user_data(self, data: Dict[str, Any]) -> None:
        """Update user data with new information."""
        self.user_data.update(data)
    
    def set_stage(self, stage: str) -> None:
        """Set the current conversation stage."""
        valid_stages = ["initial", "assessment", "protocol", "motivation", "plan", "resources"]
        if stage not in valid_stages:
            raise ValueError(f"Invalid stage. Must be one of: {', '.join(valid_stages)}")
        self.current_stage = stage
    
    def get_stage(self) -> str:
        """Get the current conversation stage."""
        return self.current_stage
    
    def get_response(self, user_input: str) -> str:
        """
        Get a response from the Bio-Age coach based on user input.
        
        Args:
            user_input: The text input from the user
            
        Returns:
            The coach's response
        """
        # Add user message to history
        self.conversation_history.append({"role": "user", "content": user_input})
        
        # Update conversation state based on user input
        self._update_state(user_input)
        
        # Check if we should prompt for more data
        if self.should_suggest_data_collection():
            next_prompt = self.get_data_assessment_prompt()
        else:
            # Get next prompt based on conversation stage
            next_prompt = self._get_stage_prompt()
        
        # Create system prompt with current user data
        system_prompt = SYSTEM_PROMPT + "\n\nCurrent user data:\n" + json.dumps(self.user_data, indent=2)
        
        # Update system message with current data
        self.conversation_history[0] = {"role": "system", "content": system_prompt}
        
        # Prepare messages for API call
        if next_prompt:
            # If we have a specific prompt for this stage, use it
            prompt_msg = {"role": "system", "content": next_prompt}
            messages_with_prompt = self.conversation_history + [prompt_msg]
        else:
            # Otherwise use the existing messages
            messages_with_prompt = self.conversation_history
        
        # Get response from OpenAI using the new API format
        response = self.mcp_client.chat.completions.create(
            model="gpt-4",
            messages=messages_with_prompt,
            temperature=0.7,
            max_tokens=800
        )
        
        # Extract response - updated for the new API format
        assistant_response = response.choices[0].message.content
        
        # Add response to message history
        self.conversation_history.append({"role": "assistant", "content": assistant_response})
        
        return assistant_response
    
    def _update_state(self, user_input: str) -> None:
        """
        Update the conversation state based on user input.
        
        This method parses user input for:
        - Biomarkers and health data
        - Habits and lifestyle information
        - Motivations
        - Responses to protocol suggestions
        
        Args:
            user_input: The user's message
        """
        # Try to extract biomarker data
        self._extract_user_data(user_input)
        
        # Extract habits (simplified for demo)
        if "habit" in user_input.lower() or "exercise" in user_input.lower() or "diet" in user_input.lower():
            for line in user_input.split('\n'):
                if line.strip().startswith('-') or line.strip().startswith('*'):
                    self.user_habits.append(line.strip()[1:].strip())
        
        # Update conversation stage based on content and current stage
        if self.current_stage == "initial":
            if len(self.user_data["biomarkers"]) > 0 or len(self.user_data["health_data"]) > 0:
                self.current_stage = "assessment"
            elif len(self.user_habits) > 0:
                self.current_stage = "habits"
                
        elif self.current_stage == "assessment":
            if "why" in user_input.lower() or "goal" in user_input.lower() or "motivation" in user_input.lower():
                self.current_stage = "motivation"
                
        # Continue updating stages as conversation progresses...
    
    def _extract_user_data(self, text: str) -> None:
        """
        Extract health data from user input and categorize it.
        
        Args:
            text: User input text
        """
        # Check for structured biomarker input
        if "my biomarker values" in text.lower():
            lines = text.split('\n')
            for line in lines:
                if line.strip().startswith('-') or line.strip().startswith('*'):
                    parts = line.strip()[1:].strip().split(':')
                    if len(parts) == 2:
                        name, value_str = parts[0].strip(), parts[1].strip()
                        
                        # Extract numeric value and unit
                        value_parts = value_str.split()
                        if len(value_parts) > 0:
                            try:
                                value = float(value_parts[0])
                                # Find which category this biomarker belongs to
                                category, item_id = self._find_biomarker_category(name)
                                if category and item_id:
                                    self.user_data[category][item_id] = value
                            except ValueError:
                                # Not a numeric value, skip
                                pass
    
    def _find_biomarker_category(self, name: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Find which category a biomarker belongs to based on its name.
        
        Args:
            name: The name of the biomarker
            
        Returns:
            Tuple of (category_key, item_id) if found, (None, None) otherwise
        """
        name_lower = name.lower()
        
        for category_key, category_data in self.protocols.get("protocols", {}).items():
            for item in category_data.get("targeted_biomarkers", []):
                if name_lower == item.get("name", "").lower() or name_lower == item.get("id", "").lower():
                    return category_key, item.get("id")
        
        return None, None
    
    def _get_stage_prompt(self) -> Optional[str]:
        """
        Get the appropriate prompt for the current conversation stage.
        
        Returns:
            Prompt text or None if no specific prompt is needed
        """
        if self.current_stage == "assessment" and self.has_sufficient_data_for_assessment():
            return BIOMARKER_ASSESSMENT_PROMPT
        elif self.current_stage == "recommendations":
            return PROTOCOL_RECOMMENDATION_PROMPT
        elif self.current_stage == "motivation":
            return MOTIVATION_EXPLORATION_PROMPT
        elif self.current_stage == "plan":
            return PLAN_CREATION_PROMPT
        elif self.current_stage == "resources":
            return RESOURCES_RECOMMENDATION_PROMPT
        
        return None
    
    def has_sufficient_data_for_assessment(self) -> bool:
        """
        Check if there is sufficient data to provide a meaningful assessment.
        
        Returns:
            True if there is enough data, False otherwise
        """
        # Either need good biomarker coverage or good functional test coverage
        biomarker_count = len(self.user_data["biomarkers"])
        bio_age_tests_count = len(self.user_data["bio_age_tests"])
        lab_results_count = len(self.user_data["lab_results"])
        
        return (biomarker_count >= 3) or (bio_age_tests_count >= 2) or (lab_results_count >= 1)
    
    def should_suggest_data_collection(self) -> bool:
        """
        Determine if we should suggest collecting more data.
        
        Returns:
            True if we should suggest more data collection, False otherwise
        """
        # Suggest data collection if overall completeness is below 40%
        # or if we're in assessment stage with limited data
        overall_completeness = self.calculate_overall_completeness()
        in_early_stages = self.current_stage in ["initial", "assessment"]
        
        return overall_completeness < 0.4 or (in_early_stages and not self.has_sufficient_data_for_assessment())
    
    def calculate_category_completeness(self, category: str) -> float:
        """
        Calculate the completeness percentage for a specific data category.
        
        Args:
            category: The category key to check
            
        Returns:
            Completeness as a value between 0.0 and 1.0
        """
        if category not in self.protocols.get("protocols", {}):
            return 0.0
        
        total_items = len(self.protocols["protocols"][category].get("targeted_biomarkers", []))
        if total_items == 0:
            return 0.0
        
        collected_items = len(self.user_data[category])
        return min(collected_items / total_items, 1.0)
    
    def calculate_overall_completeness(self) -> float:
        """
        Calculate the overall data completeness across all categories.
        
        Returns:
            Overall completeness as a value between 0.0 and 1.0
        """
        weighted_sum = 0.0
        
        for category, weight in self.category_weights.items():
            category_completeness = self.calculate_category_completeness(category)
            weighted_sum += category_completeness * weight
        
        return weighted_sum
    
    def get_data_completeness_summary(self) -> str:
        """
        Generate a summary of data completeness across all categories.
        
        Returns:
            A formatted string with completeness percentages
        """
        summary = []
        
        for category, display_data in self.protocols.get("protocols", {}).items():
            display_name = display_data.get("display_name", category)
            completeness = self.calculate_category_completeness(category)
            percentage = int(completeness * 100)
            summary.append(f"{display_name}: {percentage}% complete")
        
        overall = int(self.calculate_overall_completeness() * 100)
        summary.append(f"\nOverall Health Profile: {overall}% complete")
        
        return "\n".join(summary)
    
    def get_existing_data_summary(self) -> str:
        """
        Generate a detailed summary of the user's existing health data.
        
        Returns:
            A formatted string with the user's data across all categories
        """
        summary_parts = []
        
        # For each category
        for category_key, category_data in self.protocols.get("protocols", {}).items():
            category_display_name = category_data.get("display_name", category_key)
            user_category_data = self.user_data.get(category_key, {})
            
            # Skip empty categories
            if not user_category_data:
                continue
                
            summary_parts.append(f"\n**{category_display_name}:**")
            
            # For each item in the category that the user has data for
            for item in category_data.get("targeted_biomarkers", []):
                item_id = item.get("id")
                if item_id in user_category_data:
                    value = user_category_data[item_id]
                    item_name = item.get("name", item_id)
                    unit = item.get("unit", "")
                    
                    # Get normal range info
                    normal_range = item.get("normal_range", {})
                    min_val = normal_range.get("min", "")
                    max_val = normal_range.get("max", "")
                    optimal = normal_range.get("optimal", "")
                    
                    # Format the range string
                    range_str = ""
                    if min_val and max_val:
                        range_str = f" (normal range: {min_val}-{max_val} {unit})"
                    elif optimal:
                        range_str = f" (optimal: {optimal} {unit})"
                    
                    summary_parts.append(f"- {item_name}: {value} {unit}{range_str}")
        
        if not summary_parts:
            return "No health data found in your profile."
            
        return "\n".join(summary_parts)
    
    def get_initial_biological_age_assessment(self) -> str:
        """
        Generate an initial assessment of biological age factors based on existing data.
        
        Returns:
            A formatted string with an assessment of the user's biological age factors
        """
        # Not enough data for any assessment
        if not self.has_sufficient_data_for_assessment():
            completeness = self.calculate_overall_completeness()
            if completeness < 0.2:
                return "Insufficient data to provide a meaningful biological age assessment. Please add more measurements."
            else:
                return "Limited data available. A preliminary assessment will be possible once a few key measurements are added."
        
        assessment_parts = []
        
        # Check health data
        if self.user_data.get("health_data", {}):
            health_assessment = "Your activity metrics indicate "
            active_calories = self.user_data["health_data"].get("active_calories", 0)
            steps = self.user_data["health_data"].get("steps", 0)
            sleep = self.user_data["health_data"].get("sleep", 0)
            
            if active_calories > 500 and steps > 8000:
                health_assessment += "an active lifestyle, which is associated with lower biological age. "
            elif active_calories > 350 and steps > 5000:
                health_assessment += "a moderately active lifestyle, which is neutral to slightly positive for biological age. "
            else:
                health_assessment += "lower physical activity levels, which may contribute to accelerated biological aging. "
            
            if sleep >= 7:
                health_assessment += "Your sleep duration is optimal for cellular repair and regeneration, supporting healthy aging."
            elif sleep >= 6:
                health_assessment += "Your sleep duration is slightly below optimal, which may have minor impacts on aging processes."
            else:
                health_assessment += "Your sleep duration is below recommendations, which can accelerate biological aging."
            
            assessment_parts.append(health_assessment)
        
        # Check biomarkers
        if self.user_data.get("biomarkers", {}):
            bio_assessment = "Your biomarker profile shows "
            
            hba1c = self.user_data["biomarkers"].get("hba1c", 0)
            fasting_glucose = self.user_data["biomarkers"].get("fasting_glucose", 0)
            crp = self.user_data["biomarkers"].get("crp", 0)
            
            issues = []
            if hba1c > 5.7:
                issues.append("elevated HbA1c")
            if fasting_glucose > 100:
                issues.append("elevated fasting glucose")
            if crp > 3:
                issues.append("elevated inflammation")
            
            if not issues:
                bio_assessment += "values within healthy ranges, suggesting optimal metabolic health."
            else:
                bio_assessment += f"{', '.join(issues)}, which can accelerate biological aging."
            
            assessment_parts.append(bio_assessment)
        
        # Check physical measurements
        if self.user_data.get("measurements", {}):
            meas_assessment = "Your physical measurements indicate "
            
            body_fat = self.user_data["measurements"].get("body_fat", 0)
            waist_to_height = self.user_data["measurements"].get("waist_to_height", 0)
            
            if body_fat > 25 or waist_to_height > 0.5:
                meas_assessment += "elevated body fat levels, which can contribute to metabolic aging."
            else:
                meas_assessment += "a healthy body composition, which supports optimal aging."
            
            assessment_parts.append(meas_assessment)
        
        # Check functional tests
        if self.user_data.get("bio_age_tests", {}) or self.user_data.get("capabilities", {}):
            func_assessment = "Your functional assessments suggest "
            
            # Combine bio_age_tests and capabilities
            func_values = {}
            func_values.update(self.user_data.get("bio_age_tests", {}))
            func_values.update(self.user_data.get("capabilities", {}))
            
            # Count how many are above/below average
            above_avg = 0
            below_avg = 0
            
            # Some simple rules
            if func_values.get("push_ups", 0) > 20:
                above_avg += 1
            elif func_values.get("push_ups", 0) > 0:
                below_avg += 1
                
            if func_values.get("grip_strength", 0) > 100:
                above_avg += 1
            elif func_values.get("grip_strength", 0) > 0:
                below_avg += 1
                
            if func_values.get("one_leg_stand", 0) > 30:
                above_avg += 1
            elif func_values.get("one_leg_stand", 0) > 0:
                below_avg += 1
                
            if func_values.get("vo2_max", 0) > 40:
                above_avg += 1
            elif func_values.get("vo2_max", 0) > 0:
                below_avg += 1
            
            if above_avg > below_avg:
                func_assessment += "above-average functional capacity for your age, which indicates a lower biological age."
            elif below_avg > above_avg:
                func_assessment += "room for improvement in functional capacity, which may indicate a higher biological age."
            else:
                func_assessment += "average functional capacity for your age."
            
            assessment_parts.append(func_assessment)
        
        if not assessment_parts:
            return "Unable to generate assessment with the current data."
            
        # Add summary
        overall_completeness = self.calculate_overall_completeness()
        if overall_completeness > 0.7:
            assessment_parts.append("\nOverall, your biological age appears to be approximately [X] years [above/below] your chronological age based on your comprehensive measurements.")
        elif overall_completeness > 0.4:
            assessment_parts.append("\nWith the data available, I can provide a partial assessment of your biological age factors, but more measurements would improve accuracy.")
        else:
            assessment_parts.append("\nThis is a preliminary assessment based on limited data. Adding more measurements would significantly improve the accuracy of your biological age estimation.")
        
        return "\n\n".join(assessment_parts)
    
    def get_data_assessment_prompt(self) -> str:
        """
        Get the appropriate data assessment prompt based on completeness.
        
        Returns:
            Formatted prompt with user data inserted
        """
        completeness = self.calculate_overall_completeness()
        completeness_percentage = int(completeness * 100)
        
        existing_data_summary = self.get_existing_data_summary()
        initial_assessment = self.get_initial_biological_age_assessment()
        missing_data = self.format_missing_data_suggestions()
        
        # Select the appropriate prompt based on completeness
        if completeness < 0.2:
            prompt = CRITICAL_DATA_PROMPT.format(
                existing_data_summary=existing_data_summary,
                missing_high_value_data=missing_data,
                completeness_percentage=completeness_percentage
            )
        elif completeness < 0.5:
            # Estimate projected completeness if they add suggested measurements
            suggested_count = min(5, 10 - int(completeness * 10))  # Suggest enough to get to 50%
            projected_completeness = min(100, completeness_percentage + suggested_count * 10)
            
            prompt = HIGH_IMPACT_GAPS_PROMPT.format(
                existing_data_summary=existing_data_summary,
                initial_assessment=initial_assessment,
                missing_high_value_data=missing_data,
                completeness_percentage=completeness_percentage,
                projected_completeness=projected_completeness
            )
        elif completeness < 0.8:
            prompt = REFINEMENT_DATA_PROMPT.format(
                existing_data_summary=existing_data_summary,
                initial_assessment=initial_assessment,
                missing_high_value_data=missing_data,
                completeness_percentage=completeness_percentage
            )
        else:
            prompt = COMPREHENSIVE_ANALYSIS_PROMPT.format(
                existing_data_summary=existing_data_summary,
                detailed_assessment=initial_assessment,
                completeness_percentage=completeness_percentage
            )
        
        return prompt
    
    def suggest_next_measurements(self, limit: int = 3) -> List[Dict]:
        """
        Suggest the next most valuable measurements the user should take.
        
        Args:
            limit: Maximum number of suggestions to return
            
        Returns:
            List of suggested measurements with category and item details
        """
        suggestions = []
        
        # Prioritize by category completeness and item importance
        category_completeness = {
            category: self.calculate_category_completeness(category)
            for category in self.protocols.get("protocols", {}).keys()
        }
        
        # Sort categories by weighted importance and low completeness
        sorted_categories = sorted(
            category_completeness.keys(),
            key=lambda c: (
                category_completeness[c],  # Prioritize less complete categories
                -self.category_weights.get(c, 0)  # Then by category weight (higher is more important)
            )
        )
        
        for category in sorted_categories:
            if len(suggestions) >= limit:
                break
                
            category_data = self.protocols["protocols"][category]
            collected_item_ids = set(self.user_data[category].keys())
            
            # Get items not yet collected, sorted by importance
            available_items = [
                item for item in category_data.get("targeted_biomarkers", [])
                if item.get("id") not in collected_item_ids
            ]
            
            sorted_items = sorted(
                available_items,
                key=lambda item: -item.get("importance", 0)  # Higher importance first
            )
            
            # Add top items to suggestions
            for item in sorted_items:
                if len(suggestions) >= limit:
                    break
                    
                suggestions.append({
                    "category": category,
                    "category_display_name": category_data.get("display_name", category),
                    "item_id": item.get("id"),
                    "item_name": item.get("name"),
                    "description": item.get("description"),
                    "importance": item.get("importance", 0),
                    "age_impact": item.get("age_impact", "")
                })
        
        return suggestions
    
    def format_missing_data_suggestions(self, limit: int = 5) -> str:
        """
        Format the missing high-value data suggestions as a string.
        
        Args:
            limit: Maximum number of suggestions to include
            
        Returns:
            Formatted string with measurement suggestions
        """
        suggestions = self.suggest_next_measurements(limit=limit)
        
        if not suggestions:
            return "Your health profile is very complete. No additional measurements needed at this time."
        
        formatted_suggestions = []
        
        for i, suggestion in enumerate(suggestions):
            name = suggestion["item_name"]
            category = suggestion["category_display_name"]
            description = suggestion["description"]
            impact = suggestion["age_impact"]
            
            formatted_suggestions.append(f"{i+1}. **{name}** ({category})")
            formatted_suggestions.append(f"   {description}")
            if impact:
                formatted_suggestions.append(f"   Impact on biological age: {impact}")
            formatted_suggestions.append("")  # Empty line for spacing
        
        return "\n".join(formatted_suggestions)
    
    def get_biomarker_info(self, biomarker_id: str) -> Dict:
        """Get information about a specific biomarker."""
        for biomarker in self.protocols.get("protocols", {}).values():
            for item in biomarker.get("targeted_biomarkers", []):
                if item["id"] == biomarker_id:
                    return item
        return {}
    
    def get_protocol_info(self, protocol_id: str) -> Dict:
        """Get information about a specific protocol."""
        for protocol in self.protocols.get("protocols", []):
            if protocol["id"] == protocol_id:
                return protocol
        return {}
    
    def get_recommended_protocols(self) -> List[Dict]:
        """Get protocols recommended for the user based on their biomarkers."""
        if not self.user_data["biomarkers"]:
            return []
        
        # Simple recommendation algorithm
        recommended = []
        for protocol in self.protocols.get("protocols", []):
            # Check if protocol targets any of the user's biomarkers
            targets = protocol.get("targeted_biomarkers", [])
            for biomarker_id in self.user_data["biomarkers"]:
                if biomarker_id in targets:
                    recommended.append(protocol)
                    break
        
        return recommended
    
    def _get_user_data_context(self) -> str:
        """Get a formatted string of relevant user data context."""
        if not self.user_data:
            return "No user data available."
        
        context = "Available User Data:\n"
        
        # Basic demographics
        if "demographics" in self.user_data:
            demographics = self.user_data["demographics"]
            context += "\nDemographics:\n"
            for key, value in demographics.items():
                context += f"- {key}: {value}\n"
        
        # Health metrics with units and normal ranges
        if "health_metrics" in self.user_data:
            metrics = self.user_data["health_metrics"]
            context += "\nHealth Metrics (with normal ranges):\n"
            for category, data in metrics.items():
                if isinstance(data, dict):
                    context += f"- {category}:\n"
                    for key, value in data.items():
                        # Add normal ranges for key metrics
                        range_info = ""
                        if key == "hba1c":
                            range_info = " (Normal < 5.7%, Prediabetic 5.7-6.4%, Diabetic > 6.4%)"
                        elif key == "fasting_glucose":
                            range_info = " (Normal < 100 mg/dL, Prediabetic 100-125 mg/dL, Diabetic > 125 mg/dL)"
                        elif key == "sleep_hours":
                            range_info = " (Recommended: 8-10 hours for ages 18-25)"
                        context += f"  - {key}: {value}{range_info}\n"
                else:
                    context += f"- {category}: {data}\n"
        
        # Fitness metrics with age/sex-specific standards
        if "fitness_metrics" in self.user_data:
            fitness = self.user_data["fitness_metrics"]
            context += "\nFitness Metrics (with age/sex standards):\n"
            for key, value in fitness.items():
                # Add standards for key metrics
                standards_info = ""
                if key == "push_ups" and "demographics" in self.user_data:
                    age = self.user_data["demographics"].get("age")
                    sex = self.user_data["demographics"].get("sex")
                    if age and sex and 18 <= age <= 20 and sex.lower() == "male":
                        standards_info = " (Standards for men 18-20: Poor < 10, Below Average 11-14, Average 15-20, Above Average 21-25, Excellent > 25)"
                elif key == "grip_strength" and "demographics" in self.user_data:
                    age = self.user_data["demographics"].get("age")
                    sex = self.user_data["demographics"].get("sex")
                    if age and sex and 18 <= age <= 20 and sex.lower() == "male":
                        standards_info = " (Standards for men 18-20: Poor < 30 kg, Average 30-50 kg, Excellent > 70 kg)"
                context += f"- {key}: {value}{standards_info}\n"
        
        # Sleep and recovery with recommendations
        if "sleep_metrics" in self.user_data:
            sleep = self.user_data["sleep_metrics"]
            context += "\nSleep and Recovery (with recommendations):\n"
            for key, value in sleep.items():
                # Add recommendations for key metrics
                rec_info = ""
                if key == "sleep_duration":
                    rec_info = " (Recommended: 7-9 hours for adults)"
                elif key == "sleep_quality":
                    rec_info = " (Target: > 85%)"
                context += f"- {key}: {value}{rec_info}\n"
        
        return context

    def _get_base_prompt(self) -> str:
        """Get the base system prompt for the coach."""
        base_prompt = """You are a Bio Age Coach, an expert in biological age assessment and optimization. Your role is to:
        1. Analyze and interpret health metrics in relation to biological age
        2. Provide accurate, evidence-based assessments of fitness and health metrics
        3. Focus on age and sex-specific standards when evaluating performance
        4. Maintain a professional yet encouraging tone
        5. Keep responses concise and directly relevant to the user's questions
        
        When discussing metrics:
        - Compare to established age/sex-specific standards
        - Cite specific ranges and values from the research
        - Explain how different metrics interact
        - Avoid making unsupported claims
        """
        return base_prompt 