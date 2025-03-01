"""
Example script demonstrating how to use the Epistemic Me SDK with a simulated user.
"""

import epistemic_me
import os
from epistemic_me.generated.proto.models.dialectic_pb2 import DialecticType
from dialectic_harness.user_simulator import UserSimulator

# Define beliefs for the simulated user
HEALTH_BELIEFS = {
    "sleep": [
        "my energy levels are much higher when I maintain a consistent 10pm bedtime",
        "using my phone before bed disrupts my sleep, so I stop all screen time by 9pm",
        "my morning routine works best when I wake up naturally without an alarm"
    ],
    "exercise": [
        "alternating between running and strength training gives me the best results",
        "tracking my workouts in a fitness app helps me stay motivated and consistent",
        "taking a rest day after intense workouts helps prevent burnout and injury"
    ],
    "mental_health": [
        "doing a 10-minute meditation each morning helps me stay focused all day",
        "journaling about my emotions helps me understand my stress triggers",
        "regular walks in nature significantly improve my mood and clarity"
    ],
    "daily_habits": [
        "preparing healthy meals on Sunday sets me up for a successful week",
        "using a habit tracker app has helped me build consistent routines",
        "small daily choices like taking the stairs add up to big health improvements"
    ]
}

def run_simulated_session():
    """Run a simulated dialectic learning session using the Epistemic Me SDK."""
    
    # Initialize the SDK client
    epistemic_me.set_base_url("localhost:8080")

    # Create a developer
    developer_name = "Test Developer"
    developer_email = "test_user@example.com"
    developer = epistemic_me.Developer.create(name=developer_name, email=developer_email)
    
    # Set the API key in the config for subsequent calls
    epistemic_me.config.api_key = developer["apiKeys"][0]
    
    # Initialize the user simulator
    simulator = UserSimulator(
        beliefs=HEALTH_BELIEFS,
        personality_traits={
            "consistency": 0.9,
            "verbosity": 0.7,
            "certainty": 0.8
        },
        api_key=os.getenv("OPENAI_API_KEY")  # Get API key from environment
    )
    
    try:
        # Create a new dialectic
        dialectic_response = epistemic_me.Dialectic.create(
            self_model_id="simulated_user",
            dialectic_type=DialecticType.DEFAULT
        )
        dialectic = dialectic_response["dialectic"]
        print(f"\nCreated dialectic with ID: {dialectic['id']}")
        
        # Simulate interactions
        current_question = "Tell me about your health habits."  # Initial question
        max_interactions = 10  # Prevent infinite loops
        interaction_count = 0
        
        while current_question and interaction_count < max_interactions:
            interaction_count += 1
            print(f"\nInteraction {interaction_count}:")
            print(f"Question: {current_question}")
            
            # Generate response using the simulator
            answer = simulator.generate_response(current_question)
            print(f"Answer: {answer}")
            
            # Update dialectic with the Q&A interaction
            update_resp = epistemic_me.Dialectic.update(
                id=dialectic["id"],
                answer=answer,
                self_model_id="simulated_user"
            )
            
            # Get the next question from the latest interaction
            if "dialectic" in update_resp and "userInteractions" in update_resp["dialectic"]:
                interactions = update_resp["dialectic"]["userInteractions"]
                if len(interactions) > 0:
                    latest_interaction = interactions[-1]
                    if (latest_interaction["type"] == "QUESTION_ANSWER" and 
                        "interaction" in latest_interaction and 
                        "questionAnswer" in latest_interaction["interaction"] and
                        "question" in latest_interaction["interaction"]["questionAnswer"] and
                        "question" in latest_interaction["interaction"]["questionAnswer"]["question"]):
                        current_question = latest_interaction["interaction"]["questionAnswer"]["question"]["question"]
                    else:
                        print("No more questions available")
                        break
                else:
                    print("No interactions found")
                    break
            else:
                print("Invalid response structure")
                break

        print(f"\nCompleted {interaction_count} interactions")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_simulated_session()