"""
Core implementation of the BioAgeCoach chatbot.
"""

import json
import os
from typing import Dict, List, Optional, Tuple, Any
from openai import OpenAI
from dotenv import load_dotenv

from .prompts import (
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

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class BioAgeCoach:
    """
    AI Coach for biological age optimization.
    
    This class manages the conversation flow and state for the Bio Age Coach chatbot.
    """
    
    def __init__(self):
        """Initialize the Bio Age Coach."""
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.messages = []
        
        # Initialize empty user data structure
        self.user_data = {
            "health_data": {},
            "bio_age_tests": {},
            "capabilities": {},
            "biomarkers": {},
            "measurements": {},
            "lab_results": {}
        }
        
        # Load biomarkers data
        try:
            with open("data/biomarkers.json", "r") as f:
                self.biomarkers = json.load(f)
        except Exception as e:
            print(f"Error loading data/biomarkers.json: {e}")
            # Use default biomarkers if file can't be loaded
            self.biomarkers = {
                "categories": {
                    "health_data": {
                        "display_name": "Daily Health Data",
                        "items": [
                            {"id": "active_calories", "name": "Active Calories", "unit": "kcal"},
                            {"id": "steps", "name": "Steps", "unit": "steps"},
                            {"id": "sleep", "name": "Sleep Duration", "unit": "hours"},
                            {"id": "resting_heart_rate", "name": "Resting Heart Rate", "unit": "bpm"}
                        ]
                    },
                    "bio_age_tests": {
                        "display_name": "Bio-Age Tests",
                        "items": [
                            {"id": "push_ups", "name": "Push-ups", "unit": "reps"},
                            {"id": "grip_strength", "name": "Grip Strength", "unit": "kg"},
                            {"id": "one_leg_stand", "name": "One-Leg Stand", "unit": "seconds"}
                        ]
                    },
                    "biomarkers": {
                        "display_name": "Biomarkers",
                        "items": [
                            {"id": "hba1c", "name": "HbA1c", "unit": "%"},
                            {"id": "hdl", "name": "HDL Cholesterol", "unit": "mg/dL"},
                            {"id": "ldl", "name": "LDL Cholesterol", "unit": "mg/dL"}
                        ]
                    }
                }
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
        self.conversation_stage = "introduction"
        
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
        self.messages.append({"role": "system", "content": SYSTEM_PROMPT})
        
    def reset(self):
        """Reset the conversation state."""
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        self.user_data = {
            "health_data": {},
            "bio_age_tests": {},
            "capabilities": {},
            "biomarkers": {},
            "measurements": {},
            "lab_results": {}
        }
        self.user_habits = []
        self.user_motivations = []
        self.recommended_protocols = []
        self.conversation_stage = "introduction"
    
    def get_response(self, user_input: str) -> str:
        """
        Get a response from the Bio-Age coach based on user input.
        
        Args:
            user_input: The text input from the user
            
        Returns:
            The coach's response
        """
        # Add user message to history
        self.messages.append({"role": "user", "content": user_input})
        
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
        self.messages[0] = {"role": "system", "content": system_prompt}
        
        # Prepare messages for API call
        if next_prompt:
            # If we have a specific prompt for this stage, use it
            prompt_msg = {"role": "system", "content": next_prompt}
            messages_with_prompt = self.messages + [prompt_msg]
        else:
            # Otherwise use the existing messages
            messages_with_prompt = self.messages
        
        # Get response from OpenAI using the new API format
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=messages_with_prompt,
            temperature=0.7,
            max_tokens=800
        )
        
        # Extract response - updated for the new API format
        assistant_response = response.choices[0].message.content
        
        # Add response to message history
        self.messages.append({"role": "assistant", "content": assistant_response})
        
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
        if self.conversation_stage == "introduction":
            if len(self.user_data["biomarkers"]) > 0 or len(self.user_data["health_data"]) > 0:
                self.conversation_stage = "assessment"
            elif len(self.user_habits) > 0:
                self.conversation_stage = "habits"
                
        elif self.conversation_stage == "assessment":
            if "why" in user_input.lower() or "goal" in user_input.lower() or "motivation" in user_input.lower():
                self.conversation_stage = "motivation"
                
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
        
        for category_key, category_data in self.biomarkers.get("categories", {}).items():
            for item in category_data.get("items", []):
                if name_lower == item.get("name", "").lower() or name_lower == item.get("id", "").lower():
                    return category_key, item.get("id")
        
        return None, None
    
    def _get_stage_prompt(self) -> Optional[str]:
        """
        Get the appropriate prompt for the current conversation stage.
        
        Returns:
            Prompt text or None if no specific prompt is needed
        """
        if self.conversation_stage == "assessment" and self.has_sufficient_data_for_assessment():
            return BIOMARKER_ASSESSMENT_PROMPT
        elif self.conversation_stage == "recommendations":
            return PROTOCOL_RECOMMENDATION_PROMPT
        elif self.conversation_stage == "motivation":
            return MOTIVATION_EXPLORATION_PROMPT
        elif self.conversation_stage == "plan":
            return PLAN_CREATION_PROMPT
        elif self.conversation_stage == "resources":
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
        in_early_stages = self.conversation_stage in ["introduction", "assessment"]
        
        return overall_completeness < 0.4 or (in_early_stages and not self.has_sufficient_data_for_assessment())
    
    def calculate_category_completeness(self, category: str) -> float:
        """
        Calculate the completeness percentage for a specific data category.
        
        Args:
            category: The category key to check
            
        Returns:
            Completeness as a value between 0.0 and 1.0
        """
        if category not in self.biomarkers.get("categories", {}):
            return 0.0
        
        total_items = len(self.biomarkers["categories"][category].get("items", []))
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
        
        for category, display_data in self.biomarkers.get("categories", {}).items():
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
        for category_key, category_data in self.biomarkers.get("categories", {}).items():
            category_display_name = category_data.get("display_name", category_key)
            user_category_data = self.user_data.get(category_key, {})
            
            # Skip empty categories
            if not user_category_data:
                continue
                
            summary_parts.append(f"\n**{category_display_name}:**")
            
            # For each item in the category that the user has data for
            for item in category_data.get("items", []):
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
            
            # Physical activity assessment
            if active_calories > 500 and steps > 8000:
                health_assessment += "an active lifestyle, which is associated with lower biological age. "
            elif active_calories > 350 and steps > 5000:
                health_assessment += "a moderately active lifestyle, which is neutral to slightly positive for biological age. "
            else:
                health_assessment += "lower physical activity levels, which may contribute to accelerated biological aging. "
            
            # Sleep assessment
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
            for category in self.biomarkers.get("categories", {}).keys()
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
                
            category_data = self.biomarkers["categories"].get(category, {})
            collected_item_ids = set(self.user_data[category].keys())
            
            # Get items not yet collected, sorted by importance
            available_items = [
                item for item in category_data.get("items", [])
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
        for biomarker in self.biomarkers.get("biomarkers", []):
            if biomarker["id"] == biomarker_id:
                return biomarker
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