from typing import List, Dict
import uuid
from dataclasses import asdict
from datetime import datetime
import random

from deepeval.dataset import EvaluationDataset
from deepeval.test_case import LLMTestCase, ConversationalTestCase

from src.models.conversation import Conversation, Turn, ConversationMetrics
from src.models.context import EvaluationContext

class DatasetGenerator:
    def __init__(self):
        self.sample_beliefs = {
            "health_important": 0.8,
            "exercise_beneficial": 0.7,
            "aging_controllable": 0.6,
            "nutrition_impacts_health": 0.75,
            "sleep_quality_matters": 0.85,
            "stress_management_critical": 0.65,
            "preventive_care_valuable": 0.7,
            "lifestyle_choices_matter": 0.8
        }

        self.sample_cohorts = [
            "health_conscious_professional",
            "fitness_enthusiast",
            "wellness_beginner",
            "health_skeptic"
        ]

        self.sample_router_intents = [
            "Lower BioAge Score",
            "Query Health Analysis",
            "Research Health",
            "View Health Data as Visualization"
        ]

    def generate_sample_context(self) -> dict:
        """Generate a sample context for a conversation"""
        return {
            "user_cohort": "health_conscious_professional",
            "router_intent": random.choice(self.sample_router_intents),
            "belief_system": ["health_important", "evidence_based_approach"],
            "demographic_data": ["age_range: 35-45", "occupation: professional"],
            "session_history": ["previous_session_1", "previous_session_2"],
            "learning_objectives": ["improve_health", "identify_lifestyle_factors"],
            "confidence_scores": {"user_identification": 0.85, "belief_understanding": 0.75}
        }

    def generate_sample_conversation(self, router_intent: str = None) -> Conversation:
        """Generate a sample conversation with appropriate context"""
        if router_intent is None:
            router_intent = random.choice(self.sample_router_intents)

        # Define intent-specific conversation templates
        intent_templates = {
            "Lower BioAge Score": [
                ("Based on your health data, I recommend focusing on these key lifestyle changes to lower your biological age: 1) Improve sleep quality by maintaining a consistent schedule, 2) Increase physical activity with both cardio and strength training, 3) Optimize your nutrition with a Mediterranean-style diet.",
                 "I want to improve my biological age. What lifestyle changes should I make?"),
                ("We can track your biological age improvements through several key metrics: sleep quality, exercise frequency, stress levels, and nutritional intake. Let's focus on implementing these changes and monitor your progress over the next few weeks.",
                 "How can I track my progress in improving my biological age?")
            ],
            "Query Health Analysis": [
                ("I've analyzed your recent health data and noticed some interesting patterns. Your cortisol levels show some elevation in the mornings, and your sleep patterns indicate room for optimization. Would you like me to break down these patterns in more detail?",
                 "Can you analyze my recent health patterns and biomarker levels?"),
                ("Looking at your latest blood test results, I notice your vitamin D levels are slightly below optimal range, while other markers are within normal ranges. Let's discuss some strategies to optimize these levels.",
                 "What do my latest blood test results indicate about my health?")
            ],
            "Research Health": [
                ("I'd be happy to help you research the relationship between stress and longevity. Research shows that chronic stress can accelerate cellular aging through various mechanisms, including telomere shortening and increased inflammation. Would you like to explore specific aspects of this topic?",
                 "I want to learn more about the impact of stress on longevity. Can you help me research this topic?"),
                ("Recent research in cognitive health has revealed several key findings: 1) The importance of social engagement in maintaining cognitive function, 2) The role of sleep in memory consolidation, and 3) The benefits of continuous learning and mental challenges. Would you like to dive deeper into any of these areas?",
                 "What are the latest research findings on improving cognitive health?")
            ],
            "View Health Data as Visualization": [
                ("I've created a visualization of your key health metrics over the past month. The graph shows your sleep quality, stress levels, and physical activity trends. I notice some interesting patterns - your sleep quality tends to improve on days with higher physical activity.",
                 "Can you visualize my health metrics trends over the past month?"),
                ("Here's a visual representation of your biomarker trends. The chart displays your cortisol, vitamin D, and inflammatory markers over time. You can see how your lifestyle changes have positively impacted these metrics.",
                 "Show me a visual comparison of my biomarker trends")
            ]
        }

        # Select conversation template based on router intent
        conversation_template = random.choice(intent_templates[router_intent])

        # Create conversation with context
        context = self._create_evaluation_context(router_intent=router_intent)
        
        # Create initial beliefs
        initial_beliefs = {
            "health_monitoring_valuable": 0.5,
            "lifestyle_impacts_aging": 0.5,
            "evidence_based_approach": 0.5,
            "data_visualization_value": 0.5
        }
        
        # Create turn with updated beliefs
        belief_updates = {
            "old": initial_beliefs.copy(),
            "new": {k: min(1.0, v + 0.2) for k, v in initial_beliefs.items()}
        }
        
        turn = Turn(
            id=str(uuid.uuid4()),
            coach_message=conversation_template[0],
            user_message=conversation_template[1],
            belief_updates=belief_updates,
            timestamp=datetime.now().timestamp()
        )

        # Create conversation
        conversation = Conversation(
            id=str(uuid.uuid4()),
            turns=[turn],
            metrics=self._create_default_metrics(),
            context=context
        )

        return conversation

    def generate_test_case(self, conversation: Conversation) -> ConversationalTestCase:
        """Convert a conversation to a DeepEval test case"""
        turns = []

        # Convert context dictionary to list of strings
        context_dict = conversation.context.to_dict()
        context = [
            f"User Cohort: {context_dict['user_cohort']}",
            f"Router Intent: {context_dict['router_intent']}",
            f"Belief System: {', '.join(str(k) for k in context_dict['belief_system'])}",
            f"Demographics: {', '.join(str(k) for k in context_dict['demographic_data'])}",
            f"Session History: {', '.join(str(session) for session in context_dict['session_history'])}",
            f"Learning Objectives: {', '.join(context_dict['learning_objectives'])}",
            f"Confidence Scores: {', '.join(f'{k}: {v}' for k, v in context_dict['confidence_scores'].items())}"
        ]

        # Convert each turn to LLMTestCase
        for turn in conversation.turns:
            llm_test_case = LLMTestCase(
                input=turn.coach_message,
                actual_output=turn.user_message,
                context=context
            )
            turns.append(llm_test_case)

        return ConversationalTestCase(turns=turns)

    def generate_evaluation_dataset(self, num_conversations: int = 5, router_intent: str = None) -> EvaluationDataset:
        """Generate a dataset with multiple conversations as an EvaluationDataset
        
        Args:
            num_conversations: Number of conversations to generate
            router_intent: Specific router intent to use for all conversations
        """
        conversations = [self.generate_sample_conversation(router_intent=router_intent) for i in range(num_conversations)]
        test_cases = [self.generate_test_case(conv) for conv in conversations]
        return EvaluationDataset(test_cases=test_cases)

    def generate_multiple_datasets(self, dataset_configs: List[Dict]) -> List[EvaluationDataset]:
        """Generate multiple named datasets"""
        datasets = []
        for i, config in enumerate(dataset_configs):
            dataset = self.generate_evaluation_dataset(
                num_conversations=config["num_conversations"],
                router_intent=config.get("router_intent")
            )
            dataset.name = config["name"]  # Add name to dataset
            datasets.append(dataset)
        return datasets

    def _create_default_metrics(self) -> ConversationMetrics:
        """Create default metrics for a conversation"""
        return ConversationMetrics(
            user_identification=0.85,
            belief_evidencing=0.75,
            belief_verification=0.80,
            ambiguity=0.15,
            learning_progress=0.70,
            answer_prediction=0.65,
            question_clarity=0.90
        )

    def _create_evaluation_context(self, router_intent: str = None) -> EvaluationContext:
        """Create a sample evaluation context"""
        if router_intent is None:
            router_intent = random.choice(self.sample_router_intents)

        return EvaluationContext(
            user_cohort="health_conscious_professional",
            router_intent=router_intent,
            belief_system=["health_important", "evidence_based_approach"],
            demographic_data=["age_range: 35-45", "occupation: professional"],
            session_history=["previous_session_1", "previous_session_2"],
            learning_objectives=["improve_health", "identify_lifestyle_factors"],
            confidence_scores={"user_identification": 0.85, "belief_understanding": 0.75}
        ) 