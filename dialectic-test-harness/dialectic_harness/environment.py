"""
Environment module for the Dialectic Test Harness.
Implements a Gym-like environment for training and evaluating dialectic learning systems.
"""

import gym
import numpy as np
import time
from typing import Dict, List, Optional, Tuple, Any
from epistemic_me.grpc_client import GrpcClient
from epistemic_me.generated.proto.models import beliefs_pb2, dialectic_pb2
from epistemic_me.dialectic import LearningObjective
from .ai_helper import BeliefAnalyzer
import os

class DialecticEnv(gym.Env):
    """
    A Gym environment for dialectic learning that implements the RL loop for question-asking
    and belief extraction.
    """
    
    def __init__(self, 
                 api_key: str,
                 grpc_api_key: str,
                 base_url: str,
                 self_model_id: str,
                 learning_objective: Dict[str, Any],
                 simulated_user_beliefs: Optional[Dict[str, Any]] = None):
        """
        Initialize the dialectic environment.
        
        Args:
            api_key: API key for OpenAI (used for belief analysis)
            grpc_api_key: API key for the Epistemic Me gRPC service
            base_url: Base URL for the gRPC service
            self_model_id: ID of the self model to use
            learning_objective: Dictionary containing learning objective parameters
            simulated_user_beliefs: Optional dictionary of simulated user beliefs for testing
        """
        super().__init__()
        
        # Initialize client and belief analyzer
        self.client = GrpcClient(base_url=base_url, api_key=grpc_api_key)
        self.belief_analyzer = BeliefAnalyzer(api_key=api_key)
        self.self_model_id = self_model_id
        
        # Set up learning objective using SDK's class
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
        # Create new dialectic session using gRPC client
        response = self.client.create_dialectic(
            id=self.self_model_id,
            learning_objective=self.learning_objective,
            dialectic_type=dialectic_pb2.DialecticType.DEFAULT
        )
        
        # Extract initial state from response dictionary
        dialectic = response["dialectic"]
        self.dialectic_id = dialectic["id"]
        self.episode_step = 0
        self.current_state = self._extract_state(dialectic)
        
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
        
        # Create user answer proto
        user_answer = dialectic_pb2.UserAnswer(
            user_answer=answer,
            created_at_millis_utc=int(time.time() * 1000)
        )
        
        # Submit answer using gRPC client
        response = self.client.update_dialectic(
            id=self.dialectic_id,
            answer=user_answer,
            self_model_id=self.self_model_id
        )
        
        # Update state from response dictionary
        dialectic = response["dialectic"]
        new_state = self._extract_state(dialectic)
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
                "completion_percentage": dialectic_data["learningObjective"]["completionPercentage"]
            },
            belief_system=belief_system
        )
        
        return {
            "question": self._get_current_question(dialectic_data),
            "beliefs_extracted": len(belief_system["beliefs"]),
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
                        "content": belief.get("content", [{}])[0].get("rawStr", ""),
                        "type": belief.get("type", "STATEMENT"),
                        "evidence": {
                            "type": belief.get("evidence", {}).get("type", "NONE"),
                            "content": belief.get("evidence", {}).get("content", "")
                        }
                    })
        return {"beliefs": beliefs}

    def _get_current_question(self, dialectic_data: Optional[Dict] = None) -> str:
        """Get the current question from the dialectic data."""
        data = dialectic_data or self.current_state
        if not data or "userInteractions" not in data:
            return ""
            
        interactions = data["userInteractions"]
        if not interactions:
            return ""
            
        latest = interactions[-1]
        return (
            latest.get("interaction", {})
            .get("questionAnswer", {})
            .get("question", {})
            .get("question", "")
        )

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

class DialecticEnvironment:
    def __init__(self, openai_api_key, epistemic_me_api_key=None, base_url='localhost:8080', self_model_id='test-health-philosophy-user'):
        """Initialize the environment with API keys.
        
        Args:
            openai_api_key (str): API key for OpenAI
            epistemic_me_api_key (str, optional): API key for Epistemic Me. If not provided, 
                                                a new developer will be created.
            base_url (str, optional): Base URL for the gRPC server. Defaults to localhost:8080.
            self_model_id (str, optional): ID of the self model to use. Defaults to test-health-philosophy-user.
        """
        self.openai_api_key = openai_api_key
        self.self_model_id = self_model_id
        
        # Initialize gRPC client and create developer if needed
        if not epistemic_me_api_key:
            temp_client = GrpcClient(base_url, 'temp_key')
            developer = temp_client.create_developer(
                name='Test Developer',
                email='test@example.com'
            )
            self.epistemic_me_api_key = developer['apiKeys'][0]
        else:
            self.epistemic_me_api_key = epistemic_me_api_key
            
        self.client = GrpcClient(base_url, self.epistemic_me_api_key)
        
        # Initialize learning objective using SDK's class
        self.learning_objective = LearningObjective(
            description="to learn my user's beliefs about sleep, diet and exercise including daily habits and the influences on their health beliefs",
            topics=["sleep", "diet", "exercise", "health habits"],
            target_belief_type="STATEMENT"
        )
        
        # Set up self model with philosophy and belief system
        self._setup_self_model()

    def _setup_self_model(self):
        """Set up self model with philosophy and belief system."""
        # Create self model if it doesn't exist
        self.create_self_model()

    def create_self_model(self):
        """Create a self model if it doesn't exist."""
        try:
            # First try to get the existing self model
            self.client.get_self_model(self.self_model_id)
            print(f"Self model {self.self_model_id} already exists")
            return
        except Exception as e:
            # Only create a new self model if it doesn't exist
            print(f"Creating self model {self.self_model_id}")
            self.client.create_self_model(self.self_model_id, ["life live to be healthy but comfortable"])
            print(f"Created self model {self.self_model_id}")
            time.sleep(2)  # Wait for self model to be created

            # Verify self model was created
            max_retries = 5
            for i in range(max_retries):
                try:
                    self.client.get_self_model(self.self_model_id)
                    print(f"Verified self model {self.self_model_id} exists")
                    break
                except Exception as e:
                    if i == max_retries - 1:
                        raise Exception(f"Failed to verify self model creation after {max_retries} retries: {e}")
                    print(f"Waiting for self model to be created (attempt {i + 1}/{max_retries})")
                    time.sleep(2)

            # Create initial beliefs
            print("Creating initial beliefs...")
            initial_beliefs = [
                "I believe in taking care of my health",
                "I try to maintain a balanced lifestyle",
                "Regular exercise is important to me"
            ]

            # Create each belief
            for belief in initial_beliefs:
                try:
                    self.client.create_belief(
                        self_model_id=self.self_model_id,
                        belief_content=belief
                    )
                    print(f"Created belief: {belief}")
                    time.sleep(2)  # Wait between creating beliefs
                except Exception as e:
                    print(f"Error creating belief '{belief}': {e}")

            # Verify beliefs were created
            print("Verifying beliefs...")
            max_retries = 5
            for i in range(max_retries):
                try:
                    # Try to get the beliefs
                    beliefs = self.client.list_beliefs(self_model_id=self.self_model_id)
                    if beliefs and len(beliefs) >= len(initial_beliefs):
                        print(f"Created {len(beliefs)} initial beliefs")
                        break
                    print(f"Waiting for beliefs to be created ({len(beliefs)}/{len(initial_beliefs)})")
                except Exception as e:
                    if i == max_retries - 1:
                        raise Exception(f"Failed to verify belief creation after {max_retries} retries: {e}")
                    print(f"Waiting for beliefs to be created (attempt {i + 1}/{max_retries})")
                    time.sleep(2)

            # Final wait to ensure everything is processed
            print("Waiting for final processing...")
            time.sleep(3)
            print("Setup complete")
            return
        except Exception as e:
            print(f"Creating self model {self.self_model_id}")
            self.client.create_self_model(self.self_model_id, ["life live to be healthy but comfortable"])
            print(f"Created self model {self.self_model_id}")
            time.sleep(2)  # Wait for self model to be created

            # Verify self model was created
            max_retries = 5
            for i in range(max_retries):
                try:
                    self.client.get_self_model(self.self_model_id)
                    print(f"Verified self model {self.self_model_id} exists")
                    break
                except Exception as e:
                    if i == max_retries - 1:
                        raise Exception(f"Failed to verify self model creation after {max_retries} retries: {e}")
                    print(f"Waiting for self model to be created (attempt {i + 1}/{max_retries})")
                    time.sleep(2)

            # Create initial beliefs
            print("Creating initial beliefs...")
            initial_beliefs = [
                "I believe in taking care of my health",
                "I try to maintain a balanced lifestyle",
                "Regular exercise is important to me"
            ]

            # Create each belief
            for belief in initial_beliefs:
                try:
                    self.client.create_belief(
                        self_model_id=self.self_model_id,
                        belief_content=belief
                    )
                    print(f"Created belief: {belief}")
                    time.sleep(2)  # Wait between creating beliefs
                except Exception as e:
                    print(f"Error creating belief '{belief}': {e}")

            # Verify beliefs were created
            print("Verifying beliefs...")
            max_retries = 5
            for i in range(max_retries):
                try:
                    # Try to get the beliefs
                    beliefs = self.client.list_beliefs(self_model_id=self.self_model_id)
                    if beliefs and len(beliefs) >= len(initial_beliefs):
                        print(f"Created {len(beliefs)} initial beliefs")
                        break
                    print(f"Waiting for beliefs to be created ({len(beliefs)}/{len(initial_beliefs)})")
                except Exception as e:
                    if i == max_retries - 1:
                        raise Exception(f"Failed to verify belief creation after {max_retries} retries: {e}")
                    print(f"Waiting for beliefs to be created (attempt {i + 1}/{max_retries})")
                    time.sleep(2)

            # Final wait to ensure everything is processed
            print("Waiting for final processing...")
            time.sleep(3)
            print("Setup complete")

    def _verify_self_model(self):
        """Verify that the self model exists and recreate if needed."""
        try:
            self.client.get_self_model(id=self.self_model_id)
            return True
        except:
            print("Self model not found, recreating...")
            self._setup_self_model()
            return True

    def create_dialectic(self):
        """Create a new dialectic session."""
        # Verify self model exists before creating dialectic
        self._verify_self_model()
        
        response = self.client.create_dialectic(
            id=self.self_model_id,
            learning_objective=self.learning_objective
        )
        
        # Extract dialectic from response
        dialectic = response.get('dialectic', {})
        user_interactions = dialectic.get('userInteractions', [])
        
        # Get the first question
        next_question = ""
        for interaction in user_interactions:
            if interaction.get('status') == 'PENDING_ANSWER':
                qa = interaction.get('interaction', {}).get('questionAnswer', {})
                if qa and qa.get('question', {}).get('question'):
                    next_question = qa['question']['question']
                    break
        
        return {
            'id': dialectic.get('id', ''),
            'nextQuestion': next_question,
            'userInteractions': user_interactions
        }

    def update_dialectic(self, dialectic_id, answer):
        """Update the dialectic with a user answer."""
        # Verify self model exists before updating
        self._verify_self_model()
        
        # Create user answer proto
        user_answer = dialectic_pb2.UserAnswer(
            user_answer=answer,
            created_at_millis_utc=int(time.time() * 1000)
        )
        
        response = self.client.update_dialectic(
            id=dialectic_id,
            answer=user_answer,
            self_model_id=self.self_model_id
        )
        
        # Extract dialectic from response
        dialectic = response.get('dialectic', {})
        user_interactions = dialectic.get('userInteractions', [])
        
        # Get the latest interaction that's pending an answer
        next_question = ""
        for interaction in reversed(user_interactions):
            if interaction.get('status') == 'PENDING_ANSWER':
                qa = interaction.get('interaction', {}).get('questionAnswer', {})
                if qa and qa.get('question', {}).get('question'):
                    next_question = qa['question']['question']
                    break
        
        return {
            'id': dialectic.get('id', ''),
            'nextQuestion': next_question,
            'userInteractions': user_interactions
        }

def run_simulated_session(openai_api_key=None):
    """Run a simulated dialectic session.
    
    Args:
        openai_api_key (str, optional): API key for OpenAI. If not provided, will use environment variable.
    """
    # Get OpenAI API key from environment if not provided
    if not openai_api_key:
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
    
    # Create environment - this will automatically create a new developer
    env = DialecticEnvironment(openai_api_key)
    print("\nCreated new developer with API key:", env.epistemic_me_api_key)
    
    # Create dialectic
    dialectic = env.create_dialectic()
    print(f"\nCreated dialectic with ID: {dialectic['id']}")
    print(f"First question: {dialectic['nextQuestion']}\n")
    
    # Simulate some interactions
    answers = [
        "I try to get 8 hours of sleep each night and maintain a consistent schedule",
        "I eat a balanced diet with plenty of vegetables and limit processed foods",
        "I exercise 3-4 times per week, mixing cardio and strength training",
        "I believe in preventive healthcare and regular check-ups",
        "I practice stress management through meditation and yoga",
        "I stay hydrated and avoid caffeine late in the day for better sleep",
        "I take rest days between workouts for proper recovery",
        "I monitor my mental health as much as my physical health"
    ]
    
    for i, answer in enumerate(answers, 1):
        print(f"Interaction {i}:")
        print(f"Answer: {answer}")
        response = env.update_dialectic(dialectic['id'], answer)
        print(f"Next question: {response['nextQuestion']}\n")

if __name__ == '__main__':
    run_simulated_session() 