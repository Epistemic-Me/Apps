"""
Example script demonstrating AI Coach training through simulated dialectic sessions.
This script trains an AI Coach to generate effective questions and understand user responses
through interactions with a simulated user.

The script implements:
1. Self-models for both AI Coach and User
2. Question generation and evaluation
3. Reward-based learning for question-answer effectiveness
4. Progress tracking towards learning objectives
"""

import os
import uuid
import json
import time
from typing import Dict, List, Optional

import epistemic_me
from epistemic_me.dialectic import LearningObjective
from dialectic_harness.ai_helper import BeliefAnalyzer
from dialectic_harness.user_simulator import UserSimulator
from epistemic_me.generated.proto.models.dialectic_pb2 import DialecticType
from epistemic_me.generated.proto.models.beliefs_pb2 import BeliefType

# Define the AI Coach's self-model philosophy
AI_COACH_PHILOSOPHY = {
    "role": "health and wellness coach",
    "principles": [
        "Ask open-ended questions that encourage reflection",
        "Build on previous responses to deepen understanding",
        "Focus on personal experiences and observed outcomes",
        "Help users identify patterns and connections",
        "Maintain a supportive and non-judgmental stance"
    ],
    "question_strategies": [
        "Start broad and narrow down based on responses",
        "Use follow-up questions to explore specific aspects",
        "Connect different areas of health and wellness",
        "Explore both successes and challenges",
        "Encourage forward-thinking and goal-setting"
    ]
}

# Define the simulated User's self-model
USER_SELF_MODEL = {
    "personality": {
        "openness": 0.8,  # Open to new ideas and experiences
        "consistency": 0.7,  # Moderately consistent in habits
        "reflection": 0.9,  # Highly reflective about experiences
        "detail_orientation": 0.6  # Moderately detailed in responses
    },
    "communication_style": {
        "verbosity": 0.7,  # Moderately detailed responses
        "personal_examples": 0.8,  # Often provides personal examples
        "emotional_expression": 0.6  # Moderate emotional expression
    },
    "learning_preferences": {
        "experiential": 0.9,  # Learns best from experience
        "analytical": 0.7,  # Moderately analytical
        "practical": 0.8  # Prefers practical applications
    }
}

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

def calculate_question_reward(question, answer, learning_objective):
    """Calculate a reward score for a question-answer pair based on learning objective progress."""
    analyzer = BeliefAnalyzer()
    
    # Analyze the answer for belief content
    belief = {
        "content": answer,
        "type": "STATEMENT",
        "evidence": {"type": "EXPERIENCE", "content": answer},
        "topic": determine_topic(answer),
        "confidence": assess_confidence(answer)
    }
    
    # Calculate various components of the reward
    topic_coverage = analyzer.calculate_topic_coverage([belief], learning_objective.topics)
    insight_quality = analyzer.assess_insight_quality(belief)
    personal_relevance = analyzer.assess_personal_relevance(belief)
    
    # Combine components into final reward
    reward = (
        0.4 * topic_coverage +  # Weight for topic coverage
        0.3 * insight_quality +  # Weight for quality of insights
        0.3 * personal_relevance  # Weight for personal relevance
    )
    
    return reward

def generate_follow_up_question(previous_qa_pairs, learning_objective):
    """Generate a follow-up question based on previous interactions and learning objective."""
    # Implement question generation logic here
    # This would typically use the AI Coach's philosophy and previous interactions
    # to generate an appropriate follow-up question
    pass

def run_simulated_analysis_session():
    """Run a simulated dialectic learning session for AI Coach training."""
    
    # Initialize the SDK client
    epistemic_me.set_base_url("localhost:8080")

    # Create a developer
    developer_name = "Test Developer"
    developer_email = "test_user@example.com"
    developer = epistemic_me.Developer.create(name=developer_name, email=developer_email)
    
    # Set the API key in the config for subsequent calls
    epistemic_me.config.api_key = developer["apiKeys"][0]
    
    # Create self model for the simulated user
    user_id = "simulated_user_" + str(uuid.uuid4())
    user_model = epistemic_me.SelfModel.create(id=user_id)
    print(f"\nCreated User self model with ID: {user_id}")
    
    # Create learning objective
    learning_objective = LearningObjective(
        description="Train AI Coach to effectively explore and understand user's health habits",
        topics=["sleep", "exercise", "mental_health", "daily_habits"],
        target_belief_type=BeliefType.STATEMENT
    )
    
    # Add beliefs to the self model with topic information
    total_beliefs = 0
    covered_topics = set()
    
    for topic, beliefs in HEALTH_BELIEFS.items():
        covered_topics.add(topic)
        for belief in beliefs:
            belief_json = {
                "content": belief,
                "topic": topic,
                "type": "STATEMENT",
                "evidence": {"type": "EXPERIENCE", "content": belief},
                "completion_percentage": len(covered_topics) / len(learning_objective.topics) * 100,
                "quality_metrics": {
                    "clarity": 0.8,
                    "evidence": 0.7,
                    "personal_context": 0.9
                }
            }
            epistemic_me.config.grpc_client.create_belief(user_id, json.dumps(belief_json))
            total_beliefs += 1
    
    print(f"Added {total_beliefs} beliefs across {len(covered_topics)} topics")
    
    try:
        # Create a new dialectic with learning objective
        dialectic_response = epistemic_me.Dialectic.create(
            self_model_id=user_id,
            learning_objective=learning_objective,
            dialectic_type=DialecticType.DEFAULT
        )
        dialectic = dialectic_response["dialectic"]
        print(f"\nCreated dialectic with ID: {dialectic['id']}")
        
        # Initialize the user simulator
        simulator = UserSimulator(
            beliefs=HEALTH_BELIEFS,
            personality_traits={
                "consistency": 0.8,
                "verbosity": 0.7,
                "certainty": 0.8
            },
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Run the training session
        qa_pairs = []
        current_question = "Tell me about your health habits."  # Initial question
        interaction_count = 0
        max_interactions = 10
        
        while current_question and interaction_count < max_interactions:
            interaction_count += 1
            print(f"\nInteraction {interaction_count}:")
            print(f"Question: {current_question}")
            
            # Time the response generation
            start_time = time.time()
            answer = simulator.generate_response(current_question)
            response_time = time.time() - start_time
            print(f"Answer: {answer}")
            print(f"Response generation took: {response_time:.2f} seconds")
            
            # Time the dialectic update
            start_time = time.time()
            update_resp = epistemic_me.Dialectic.update(
                id=dialectic["id"],
                answer=answer,
                self_model_id=user_id
            )
            update_time = time.time() - start_time
            print(f"Dialectic update took: {update_time:.2f} seconds")
            
            # Calculate reward for this question-answer pair
            reward = calculate_question_reward(current_question, answer, learning_objective)
            
            # Store the interaction
            qa_pairs.append({
                "question": current_question,
                "answer": answer,
                "reward": reward
            })
            
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
                print("No interactions available")
                break
        
        # Analyze overall training progress
        print("\nTraining Progress Analysis:")
        print("-" * 50)
        print(f"Dialectic ID: {dialectic['id']}")
        print(f"Number of interactions: {len(qa_pairs)}")
        print("\nQuestion-Answer Pair Analysis:")
        
        for i, qa in enumerate(qa_pairs, 1):
            print(f"\nPair {i}:")
            print(f"Question: {qa['question']}")
            print(f"Reward: {qa['reward']:.2f}")
        
        # Calculate and print overall training metrics
        avg_reward = sum(qa["reward"] for qa in qa_pairs) / len(qa_pairs)
        print(f"\nOverall Training Metrics:")
        print(f"Average Reward: {avg_reward:.2f}")
            
    except Exception as e:
        print(f"Error during dialectic session: {str(e)}")

def determine_topic(response):
    """Determine the primary topic of a response."""
    topics = {
        "sleep": ["sleep", "bedtime", "rest", "wake", "alarm"],
        "exercise": ["exercise", "workout", "training", "activity", "fitness"],
        "mental_health": ["meditation", "stress", "emotion", "mood", "mental"],
        "daily_habits": ["routine", "habit", "daily", "regular", "consistent"]
    }
    
    # Count mentions of each topic
    topic_counts = {topic: sum(word in response.lower() for word in topics[topic])
                   for topic in topics}
    
    # Return the topic with the most mentions
    return max(topic_counts.items(), key=lambda x: x[1])[0]

def assess_confidence(response):
    """Assess the confidence level expressed in a response."""
    confidence_indicators = {
        "high": ["definitely", "always", "certainly", "consistently", "sure"],
        "medium": ["usually", "often", "generally", "mostly", "tend to"],
        "low": ["sometimes", "maybe", "might", "could", "possibly"]
    }
    
    # Count confidence indicators
    confidence_counts = {level: sum(word in response.lower() for word in confidence_indicators[level])
                        for level in confidence_indicators}
    
    # Return the confidence level with the most indicators
    return max(confidence_counts.items(), key=lambda x: x[1])[0]

if __name__ == "__main__":
    run_simulated_analysis_session()