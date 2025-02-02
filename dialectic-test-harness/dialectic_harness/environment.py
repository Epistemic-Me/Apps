"""
Environment module for the Dialectic Test Harness.
Implements a Gym-like environment for training and evaluating dialectic learning systems.
"""

import gym
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from epistemic_me import GrpcClient, LearningObjective, Dialectic
from epistemic_me.generated.proto.models import beliefs_pb2, dialectic_pb2
from .ai_helper import BeliefAnalyzer

class DialecticEnv(gym.Env):
    """
    A Gym environment for dialectic learning that implements the RL loop for question-asking
    and belief extraction.
    """
    
    def __init__(self, 
                 api_key: str,
                 base_url: str,
                 self_model_id: str,
                 learning_objective: Dict[str, Any],
                 simulated_user_beliefs: Optional[Dict[str, Any]] = None):
        """
        Initialize the dialectic environment.
        
        Args:
            api_key: API key for the Epistemic Me service
            base_url: Base URL for the service
            self_model_id: ID of the self model to use
            learning_objective: Dictionary containing learning objective parameters
            simulated_user_beliefs: Optional dictionary of simulated user beliefs for testing
        """
        super().__init__()
        
        # Initialize client and belief analyzer
        self.client = GrpcClient(base_url=base_url, api_key=api_key)
        self.belief_analyzer = BeliefAnalyzer(api_key=api_key)
        self.self_model_id = self_model_id
        
        # Set up learning objective
        self.learning_objective = LearningObjective(
            description=learning_objective["description"],
            topics=learning_objective["topics"],
            target_belief_type=beliefs_pb2.BeliefType.STATEMENT
        )
        
        # Store simulated beliefs if provided
        self.simulated_beliefs = simulated_user_beliefs
        
        # Initialize state
        self.dialectic_id = None
        self.current_state = None
        self.episode_step = 0
        self.max_steps = 20  # Can be made configurable
        
        # Define action and observation spaces
        self.action_space = gym.spaces.Discrete(1)  # Just "ask" action for now
        self.observation_space = gym.spaces.Dict({
            "question": gym.spaces.Text(max_length=1000),
            "beliefs_extracted": gym.spaces.Discrete(100),
            "completion_percentage": gym.spaces.Box(low=0, high=1, shape=(1,)),
            "topic_coverage": gym.spaces.Dict({
                topic: gym.spaces.Box(low=0, high=1, shape=(1,))
                for topic in learning_objective["topics"]
            })
        })

    def reset(self) -> Dict:
        """Reset the environment and start a new episode."""
        # Create new dialectic session
        response = Dialectic.create(
            self_model_id=self.self_model_id,
            learning_objective=self.learning_objective
        )
        
        # Extract initial state
        self.dialectic_id = response["dialectic"]["id"]
        self.episode_step = 0
        self.current_state = self._extract_state(response["dialectic"])
        
        return self.current_state

    def step(self, action: int) -> Tuple[Dict, float, bool, Dict]:
        """
        Take a step in the environment by asking a question and processing the answer.
        
        Args:
            action: Currently unused as we only support asking questions
            
        Returns:
            Tuple of (observation, reward, done, info)
        """
        self.episode_step += 1
        
        # Get the current question from state
        current_question = self._get_current_question()
        
        # Generate answer (either from simulation or external source)
        answer = self._generate_answer(current_question)
        
        # Submit answer and get next state
        response = Dialectic.update(
            id=self.dialectic_id,
            answer=answer,
            self_model_id=self.self_model_id
        )
        
        # Update state
        new_state = self._extract_state(response["dialectic"])
        reward = self._calculate_reward(self.current_state, new_state)
        done = self._is_episode_done(new_state)
        
        self.current_state = new_state
        
        return new_state, reward, done, {}

    def _extract_state(self, dialectic_data: Dict) -> Dict:
        """Extract relevant state information from dialectic data."""
        # Get belief system from dialectic data
        belief_system = self._extract_belief_system(dialectic_data)
        
        # Use BeliefAnalyzer to get comprehensive analysis
        analysis = self.belief_analyzer.analyze_learning_progress(
            learning_objective={
                "description": self.learning_objective.description,
                "topics": self.learning_objective.topics,
                "completion_percentage": dialectic_data.get("learningObjective", {}).get("completionPercentage", 0)
            },
            belief_system=belief_system
        )
        
        return {
            "question": self._get_current_question(dialectic_data),
            "beliefs_extracted": len(dialectic_data.get("extractedBeliefs", [])),
            "completion_percentage": analysis["completion_percentage"] / 100.0,  # Normalize to 0-1
            "topic_coverage": {
                topic: coverage["percentage"] / 100.0  # Normalize to 0-1
                for topic, coverage in analysis["topic_coverage"].items()
            },
            "quality_metrics": analysis["quality_metrics"]
        }

    def _extract_belief_system(self, dialectic_data: Dict) -> Dict[str, Any]:
        """Extract belief system from dialectic data."""
        beliefs = []
        for interaction in dialectic_data.get("userInteractions", []):
            if qa := interaction.get("interaction", {}).get("questionAnswer"):
                for belief in qa.get("extractedBeliefs", []):
                    beliefs.append({
                        "content": belief.get("content", [{"rawStr": ""}])[0].get("rawStr", ""),
                        "type": belief.get("type", "STATEMENT"),
                        "evidence": belief.get("evidence", {})
                    })
        return {"beliefs": beliefs}

    def _get_current_question(self, dialectic_data: Optional[Dict] = None) -> str:
        """Get the current question from the dialectic data."""
        data = dialectic_data or self.current_state
        if not data:
            return ""
        
        interactions = data.get("userInteractions", [])
        if not interactions:
            return ""
            
        latest = interactions[-1]
        return latest.get("interaction", {}).get("questionAnswer", {}).get("question", {}).get("question", "")

    def _generate_answer(self, question: str) -> str:
        """Generate an answer to the given question."""
        if self.simulated_beliefs:
            # TODO: Implement more sophisticated answer generation based on simulated beliefs
            return "This is a simulated answer based on beliefs"
        else:
            # In real usage, this would be replaced with actual user input
            raise NotImplementedError("Real user interaction not implemented")

    def _calculate_reward(self, old_state: Dict, new_state: Dict) -> float:
        """Calculate the reward for the transition from old_state to new_state."""
        # Reward based on increase in completion percentage
        completion_delta = (
            new_state["completion_percentage"] - 
            old_state["completion_percentage"]
        )
        
        # Reward based on improvement in topic coverage
        topic_coverage_delta = 0.0
        for topic in self.learning_objective.topics:
            old_coverage = old_state["topic_coverage"].get(topic, 0.0)
            new_coverage = new_state["topic_coverage"].get(topic, 0.0)
            topic_coverage_delta += (new_coverage - old_coverage)
        
        # Average the topic coverage delta
        if self.learning_objective.topics:
            topic_coverage_delta /= len(self.learning_objective.topics)
        
        # Combine rewards (weights can be tuned)
        reward = completion_delta * 5.0 + topic_coverage_delta * 5.0
        
        return float(reward)

    def _is_episode_done(self, state: Dict) -> bool:
        """Determine if the episode is complete."""
        return (
            self.episode_step >= self.max_steps or
            state["completion_percentage"] >= 0.95
        ) 