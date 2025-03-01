"""
User simulator module for generating realistic responses in dialectic testing.
"""

from typing import Dict, List, Optional, Set
import os
import numpy as np
from openai import OpenAI

class UserSimulator:
    """
    Simulates user responses based on a set of ground truth beliefs and personality traits.
    """
    
    # Topic keywords mapping for better belief matching
    TOPIC_KEYWORDS = {
        "sleep": {"sleep", "rest", "tired", "energy", "bedtime", "wake", "night", "morning", "nap", "screen"},
        "exercise": {"exercise", "physical", "activity", "workout", "fitness", "training", "active", "movement", "strength", "cardio"},
        "mental_health": {"mental", "emotional", "stress", "anxiety", "meditation", "mindfulness", "well-being", "mood", "balance", "reflection"},
        "daily_habits": {"habit", "routine", "daily", "practice", "consistent", "regular", "schedule", "track", "maintain", "lifestyle"}
    }
    
    def __init__(self, 
                 beliefs: Dict[str, List[str]],
                 personality_traits: Optional[Dict[str, float]] = None,
                 api_key: Optional[str] = None):
        """Initialize the user simulator."""
        self.beliefs = beliefs
        self.personality_traits = personality_traits or {
            "consistency": 0.8,
            "verbosity": 0.5,
            "certainty": 0.7
        }
        
        # Initialize OpenAI client
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key must be provided or set in OPENAI_API_KEY env var")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = "gpt-4o"  # Points to gpt-4o-2024-08-06
        
        # Track interaction history
        self.interaction_history = []
        
    def _find_relevant_beliefs(self, question: str) -> List[str]:
        """Find beliefs relevant to the given question using semantic matching."""
        relevant = []
        question_words = set(question.lower().split())
        
        # First try direct topic matching
        for topic, beliefs in self.beliefs.items():
            # Check if any topic keywords match
            if self.TOPIC_KEYWORDS[topic].intersection(question_words):
                relevant.extend(beliefs)
                continue
                
            # Check for semantic similarity with topic keywords
            topic_words = set(topic.lower().split())
            if question_words.intersection(topic_words):
                relevant.extend(beliefs)
                
        # If no direct matches, look for general health/wellness terms
        if not relevant and any(word in question_words for word in {"health", "healthy", "wellness", "well-being", "lifestyle"}):
            # Include beliefs from all topics but limit the number
            all_beliefs = []
            for beliefs in self.beliefs.values():
                all_beliefs.extend(beliefs)
            if all_beliefs:
                relevant = np.random.choice(all_beliefs, size=min(3, len(all_beliefs)), replace=False).tolist()
        
        return relevant

    def _generate_natural_response(self, template: str, question: str) -> str:
        """Generate a natural language response from the template."""
        # Create system and user messages with more detailed instructions
        messages = [
            {
                "role": "system",
                "content": (
                    "You are simulating a user's responses in a conversation about health and well-being. "
                    "Your responses should be:\n"
                    "1. Personal and experience-based, using 'I' statements\n"
                    "2. Specific and detailed, with concrete examples\n"
                    "3. Natural and conversational in tone\n"
                    "4. Focused on the question while incorporating the given beliefs\n"
                    "5. Between 2-4 sentences in length\n"
                    "Avoid being vague or theoretical - instead, share personal experiences and practical examples."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Question: {question}\n\n"
                    f"Incorporate these beliefs naturally in your response: {template}\n\n"
                    "Remember to be specific and share personal experiences that illustrate these beliefs."
                )
            }
        ]
        
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=200,
                top_p=1.0,
                frequency_penalty=0.3,
                presence_penalty=0.3
            )
            
            # Extract the response content
            if hasattr(completion.choices[0].message, 'content'):
                response = completion.choices[0].message.content
            else:
                response = str(completion.choices[0].message)
                
            return response.strip()
            
        except Exception as e:
            print(f"Warning: API call failed ({str(e)}), falling back to template")
            return template

    def _generate_uncertain_response(self, question: str) -> str:
        """Generate a response when no relevant beliefs are found."""
        # More natural uncertainty responses that acknowledge the question
        uncertainty_templates = [
            "That's an interesting question about {}. While I haven't formed a strong opinion yet, I'd be curious to hear your thoughts.",
            "I'm still developing my understanding of {}. I need more time to reflect on this aspect of health.",
            "When it comes to {}, I'm still gathering experiences and information to form a clear perspective.",
            "I appreciate you asking about {}, but I haven't fully explored that aspect of my health journey yet."
        ]
        
        # Extract key topic from question
        question_lower = question.lower()
        topic = next((word for word in question_lower.split() if any(word in keywords for keywords in self.TOPIC_KEYWORDS.values())), "this topic")
        
        return np.random.choice(uncertainty_templates).format(topic)

    def _add_inconsistency(self, response: str) -> str:
        """Add some inconsistency to the response based on personality."""
        hedges = [
            "although I've found this can vary depending on circumstances",
            "but I'm still experimenting with different approaches",
            "though I sometimes wonder if this is true for everyone",
            "even though my experience might not be universal"
        ]
        
        return f"{response}, {np.random.choice(hedges)}"

    def generate_response(self, question: str) -> str:
        """
        Generate a response to the given question based on beliefs and personality.
        
        Args:
            question: The question to answer
            
        Returns:
            A natural language response
        """
        # Find relevant beliefs
        relevant_beliefs = self._find_relevant_beliefs(question)
        
        if not relevant_beliefs:
            return self._generate_uncertain_response(question)
        
        # Select beliefs based on verbosity
        verbosity = self.personality_traits["verbosity"]
        num_beliefs = max(1, int(len(relevant_beliefs) * verbosity))
        selected_beliefs = np.random.choice(relevant_beliefs, size=min(num_beliefs, len(relevant_beliefs)), replace=False)
        
        # Create response with certainty markers
        certainty = self.personality_traits["certainty"]
        if certainty > 0.8:
            prefix = "I strongly believe that "
        elif certainty > 0.5:
            prefix = "I believe that "
        else:
            prefix = "I think that "
            
        response = prefix + " and ".join(selected_beliefs)
        
        # Generate natural language response
        response = self._generate_natural_response(response, question)
        
        # Add inconsistency if personality dictates
        if np.random.random() > self.personality_traits["consistency"]:
            response = self._add_inconsistency(response)
        
        # Track this interaction
        self.interaction_history.append({
            "question": question,
            "response": response,
            "relevant_beliefs": relevant_beliefs
        })
        
        return response

    def get_interaction_history(self) -> List[Dict]:
        """Get the history of interactions."""
        return self.interaction_history

    def reset_history(self):
        """Clear the interaction history."""
        self.interaction_history = []