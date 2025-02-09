"""
Example script demonstrating how to use the dialectic test harness with a simulated user.
"""

import os
from typing import Dict, List
import wandb
from dialectic_harness.environment import DialecticEnv
from dialectic_harness.user_simulator import UserSimulator

# Example beliefs for health-related topics
SIMULATED_BELIEFS = {
    "sleep": [
        "getting 8 hours of sleep is essential for health",
        "maintaining a consistent sleep schedule is important",
        "avoiding screens before bed helps with sleep quality",
        "naps can be beneficial if kept under 30 minutes"
    ],
    "diet": [
        "eating a balanced diet with plenty of vegetables is important",
        "processed foods should be limited",
        "regular meal times help maintain energy levels",
        "staying hydrated is crucial for health"
    ],
    "exercise": [
        "regular exercise is necessary for maintaining health",
        "a mix of cardio and strength training is ideal",
        "consistency is more important than intensity",
        "rest days are important for recovery"
    ],
    "health habits": [
        "preventive healthcare is better than reactive care",
        "mental health is as important as physical health",
        "stress management is crucial for overall wellbeing",
        "regular health check-ups are important"
    ]
}

def run_simulated_session(
    api_key: str,
    base_url: str,
    self_model_id: str,
    num_episodes: int = 5,
    log_to_wandb: bool = True
) -> Dict[str, List[float]]:
    """
    Run multiple episodes of simulated dialectic learning.
    
    Args:
        api_key: API key for the Epistemic Me service
        base_url: Base URL for the service
        self_model_id: ID of the self model to use
        num_episodes: Number of episodes to run
        log_to_wandb: Whether to log metrics to Weights & Biases
        
    Returns:
        Dictionary containing metrics for each episode
    """
    # Initialize W&B if requested
    if log_to_wandb:
        wandb.init(
            project="dialectic-learning",
            config={
                "num_episodes": num_episodes,
                "max_steps": 20,
                "personality_traits": {
                    "consistency": 0.8,
                    "verbosity": 0.5,
                    "certainty": 0.7
                }
            }
        )
    
    # Create user simulator
    simulator = UserSimulator(
        beliefs=SIMULATED_BELIEFS,
        personality_traits={
            "consistency": 0.8,
            "verbosity": 0.5,
            "certainty": 0.7
        }
    )
    
    # Create environment
    env = DialecticEnv(
        api_key=api_key,
        base_url=base_url,
        self_model_id=self_model_id,
        learning_objective={
            "description": "to learn my user's beliefs about sleep, diet and exercise including daily habits and the influences on their health beliefs",
            "topics": ["sleep", "diet", "exercise", "health habits"],
            "target_belief_type": "STATEMENT"
        }
    )
    
    # Track metrics across episodes
    metrics = {
        "episode_rewards": [],
        "episode_lengths": [],
        "final_completion": [],
        "beliefs_extracted": []
    }
    
    # Run episodes
    for episode in range(num_episodes):
        print(f"\nStarting Episode {episode + 1}/{num_episodes}")
        
        # Reset environment and simulator
        state = env.reset()
        simulator.reset_history()
        
        episode_reward = 0
        step = 0
        
        while True:
            # For now, we just use a simple "ask" action
            action = 0  # Only one action type currently
            
            # Get current question from state
            question = state["question"]
            print(f"\nQuestion: {question}")
            
            # Generate simulated response
            response = simulator.generate_response(question)
            print(f"Response: {response}")
            
            # Take step in environment
            next_state, reward, done, _ = env.step(action)
            episode_reward += reward
            step += 1
            
            # Log step metrics
            if log_to_wandb:
                wandb.log({
                    "step_reward": reward,
                    "completion_percentage": next_state["completion_percentage"],
                    "beliefs_extracted": next_state["beliefs_extracted"]
                })
            
            state = next_state
            
            if done:
                break
        
        # Record episode metrics
        metrics["episode_rewards"].append(episode_reward)
        metrics["episode_lengths"].append(step)
        metrics["final_completion"].append(state["completion_percentage"])
        metrics["beliefs_extracted"].append(state["beliefs_extracted"])
        
        # Log episode metrics
        print(f"\nEpisode {episode + 1} complete:")
        print(f"Total Reward: {episode_reward:.2f}")
        print(f"Steps: {step}")
        print(f"Completion: {state['completion_percentage']:.1%}")
        print(f"Beliefs Extracted: {state['beliefs_extracted']}")
        
        if log_to_wandb:
            wandb.log({
                "episode_reward": episode_reward,
                "episode_length": step,
                "final_completion": state["completion_percentage"],
                "total_beliefs_extracted": state["beliefs_extracted"]
            })
    
    if log_to_wandb:
        wandb.finish()
    
    return metrics

if __name__ == "__main__":
    # Get API key from environment
    api_key = os.getenv("EPISTEMIC_ME_API_KEY")
    if not api_key:
        raise ValueError("EPISTEMIC_ME_API_KEY environment variable not set")
    
    # Run simulation
    metrics = run_simulated_session(
        api_key=api_key,
        base_url="localhost:50051",  # Adjust as needed
        self_model_id="test-health-beliefs",
        num_episodes=5
    )
    
    # Print summary
    print("\nSimulation Complete!")
    print(f"Average Reward: {sum(metrics['episode_rewards']) / len(metrics['episode_rewards']):.2f}")
    print(f"Average Steps: {sum(metrics['episode_lengths']) / len(metrics['episode_lengths']):.1f}")
    print(f"Average Completion: {sum(metrics['final_completion']) / len(metrics['final_completion']):.1%}")
    print(f"Average Beliefs: {sum(metrics['beliefs_extracted']) / len(metrics['beliefs_extracted']):.1f}") 