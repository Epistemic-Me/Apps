"""
User simulator module for generating realistic responses in dialectic testing.
"""

from typing import Dict, List, Optional
import numpy as np
from transformers import pipeline

class UserSimulator:
    """
    Simulates user responses based on a set of ground truth beliefs and personality traits.
    """
    
    def __init__(self, 
                 beliefs: Dict[str, List[str]],
                 personality_traits: Optional[Dict[str, float]] = None,
                 model_name: str = "gpt2"):
        """
        Initialize the user simulator.
        
        Args:
            beliefs: Dictionary mapping topics to lists of belief statements
            personality_traits: Optional dictionary of personality parameters
                - 'consistency': How consistent the answers are (0-1)
                - 'verbosity': How detailed the answers are (0-1)
                - 'certainty': How certain the answers are (0-1)
            model_name: Name of the language model to use for response generation
        """
        self.beliefs = beliefs
        self.personality_traits = personality_traits or {
            "consistency": 0.8,
            "verbosity": 0.5,
            "certainty": 0.7
        }
        
        # Initialize language model for response generation
        self.generator = pipeline("text-generation", model=model_name)
        
        # Track interaction history
        self.interaction_history = []

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
        
        # Generate response template based on personality
        template = self._create_response_template(relevant_beliefs)
        
        # Generate natural language response
        response = self._generate_natural_response(template, question)
        
        # Add some variability based on consistency trait
        if np.random.random() > self.personality_traits["consistency"]:
            response = self._add_inconsistency(response)
        
        # Track this interaction
        self.interaction_history.append({
            "question": question,
            "response": response,
            "relevant_beliefs": relevant_beliefs
        })
        
        return response

    def _find_relevant_beliefs(self, question: str) -> List[str]:
        """Find beliefs relevant to the given question."""
        relevant = []
        
        # Simple keyword matching for now - could be improved with embeddings
        question_words = set(question.lower().split())
        
        for topic, belief_list in self.beliefs.items():
            topic_words = set(topic.lower().split())
            if question_words.intersection(topic_words):
                relevant.extend(belief_list)
                
        return relevant

    def _create_response_template(self, beliefs: List[str]) -> str:
        """Create a response template based on personality traits."""
        verbosity = self.personality_traits["verbosity"]
        certainty = self.personality_traits["certainty"]
        
        # Select number of beliefs to include based on verbosity
        num_beliefs = max(1, int(len(beliefs) * verbosity))
        selected_beliefs = np.random.choice(beliefs, size=min(num_beliefs, len(beliefs)), replace=False)
        
        # Create template with certainty markers
        if certainty > 0.8:
            prefix = "I strongly believe that "
        elif certainty > 0.5:
            prefix = "I believe that "
        else:
            prefix = "I think that "
            
        template = prefix + " and ".join(selected_beliefs)
        
        return template

    def _generate_natural_response(self, template: str, question: str) -> str:
        """Generate a natural language response from the template."""
        # Create a prompt that combines the question and template
        prompt = f"Q: {question}\nA: {template}"
        
        # Generate response with language model
        response = self.generator(
            prompt,
            max_length=150,
            num_return_sequences=1,
            temperature=0.7
        )[0]["generated_text"]
        
        # Extract just the answer portion
        response = response.split("A: ")[-1].strip()
        
        return response

    def _generate_uncertain_response(self, question: str) -> str:
        """Generate a response when no relevant beliefs are found."""
        uncertainty_templates = [
            "I'm not entirely sure about that.",
            "I haven't really thought about that before.",
            "That's an interesting question, but I'm not certain about my position.",
            "I need to think more about that topic."
        ]
        return np.random.choice(uncertainty_templates)

    def _add_inconsistency(self, response: str) -> str:
        """Add some inconsistency to the response based on personality."""
        hedges = [
            "although I sometimes think differently",
            "but I'm not entirely sure",
            "at least that's what I think today",
            "though I've changed my mind about this before"
        ]
        
        return f"{response}, {np.random.choice(hedges)}"

    def get_interaction_history(self) -> List[Dict]:
        """Get the history of interactions."""
        return self.interaction_history

    def reset_history(self):
        """Clear the interaction history."""
        self.interaction_history = [] 