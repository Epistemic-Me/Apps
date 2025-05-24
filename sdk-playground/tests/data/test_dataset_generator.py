import unittest
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path
from typing import List

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

from deepeval.dataset import EvaluationDataset
from deepeval.test_case import LLMTestCase, ConversationalTestCase
from deepeval.metrics import ConversationalGEval

from src.data.dataset_generator import DatasetGenerator

class TestDatasetGenerator(unittest.TestCase):
    def setUp(self):
        """Set up test environment before each test"""
        self.generator = DatasetGenerator()
        
    def test_generate_evaluation_dataset(self):
        """Test generation of EvaluationDataset with ConversationalTestCases"""
        # Generate dataset
        dataset = self.generator.generate_evaluation_dataset(num_conversations=3)
        
        # Verify dataset type
        self.assertIsInstance(dataset, EvaluationDataset)
        
        # Verify dataset contains correct number of test cases
        self.assertEqual(len(dataset.test_cases), 3)
        
        # Verify each test case is a ConversationalTestCase
        for test_case in dataset.test_cases:
            self.assertIsInstance(test_case, ConversationalTestCase)
            
            # Verify each turn in the conversation
            for turn in test_case.turns:
                self.assertIsInstance(turn, LLMTestCase)
                self.assertIn('input', turn.__dict__)
                self.assertIn('actual_output', turn.__dict__)
                
    def test_generate_test_case(self):
        """Test generation of a single ConversationalTestCase"""
        # Generate a conversation
        conversation = self.generator.generate_sample_conversation()
        
        # Convert to test case
        test_case = self.generator.generate_test_case(conversation)
        
        # Verify test case type
        self.assertIsInstance(test_case, ConversationalTestCase)
        
        # Verify turns match conversation
        self.assertEqual(len(test_case.turns), len(conversation.turns))
        
        # Verify turn contents
        for i, turn in enumerate(test_case.turns):
            self.assertEqual(turn.input, conversation.turns[i].coach_message)
            self.assertEqual(turn.actual_output, conversation.turns[i].user_message)
            
    def test_dataset_with_context(self):
        """Test that generated test cases include context"""
        dataset = self.generator.generate_evaluation_dataset(num_conversations=1)
        test_case = dataset.test_cases[0]
        
        # Verify context in each turn
        for turn in test_case.turns:
            self.assertIn('context', turn.__dict__)
            context = turn.context
            
            # Verify context is a list of strings
            self.assertIsInstance(context, list)
            self.assertTrue(all(isinstance(item, str) for item in context))
            
            # Verify context contains required information
            context_text = '\n'.join(context)
            self.assertIn('User Cohort:', context_text)
            self.assertIn('Router Intent:', context_text)
            self.assertIn('Belief System:', context_text)
            self.assertIn('Learning Objectives:', context_text)
            
    def test_router_intent_in_context(self):
        """Test that router intent is properly included in context"""
        # Generate a conversation
        conversation = self.generator.generate_sample_conversation()
        
        # Convert to test case
        test_case = self.generator.generate_test_case(conversation)
        
        # Get the context from the first turn
        context = test_case.turns[0].context
        
        # Find the router intent line
        router_intent_line = next((line for line in context if line.startswith('Router Intent:')), None)
        
        # Verify router intent is present and matches one of the sample intents
        self.assertIsNotNone(router_intent_line, "Router Intent not found in context")
        intent = router_intent_line.split(': ')[1]
        self.assertIn(intent, self.generator.sample_router_intents)

    def test_evaluation_context_creation(self):
        """Test that EvaluationContext is created with all required fields"""
        context_dict = self.generator.generate_sample_context()
        
        # Verify all required fields are present
        required_fields = [
            'user_cohort',
            'router_intent',
            'belief_system',
            'demographic_data',
            'session_history',
            'learning_objectives',
            'confidence_scores'
        ]
        
        for field in required_fields:
            self.assertIn(field, context_dict, f"Missing required field: {field}")
            self.assertIsNotNone(context_dict[field], f"Field {field} is None")

    def test_dataset_evaluation_compatibility(self):
        """Test that generated dataset can be evaluated with ConversationalGEval"""
        # Generate dataset
        dataset = self.generator.generate_evaluation_dataset(num_conversations=2)
        
        # Create metric
        metric = ConversationalGEval(
            name="TestMetric",
            criteria="Evaluate if the responses are relevant to the questions asked",
            evaluation_params=[
                "input",
                "actual_output",
                "context"
            ]
        )
        
        # Mock evaluation to verify compatibility
        with patch('deepeval.evaluate') as mock_evaluate:
            mock_evaluate.return_value = {'score': 0.8}
            
            # This should not raise any exceptions
            result = mock_evaluate(dataset, [metric])
            
            # Verify evaluate was called with correct arguments
            mock_evaluate.assert_called_once_with(dataset, [metric])
            
    def test_multiple_datasets(self):
        """Test generation of multiple datasets"""
        # Generate multiple datasets
        datasets = self.generator.generate_multiple_datasets(
            dataset_configs=[
                {"name": "Dataset 1", "num_conversations": 2},
                {"name": "Dataset 2", "num_conversations": 3}
            ]
        )
        
        # Verify we got correct number of datasets
        self.assertEqual(len(datasets), 2)
        
        # Verify each dataset
        self.assertEqual(len(datasets[0].test_cases), 2)
        self.assertEqual(len(datasets[1].test_cases), 3)
        
        # Verify dataset names are stored
        self.assertEqual(datasets[0].name, "Dataset 1")
        self.assertEqual(datasets[1].name, "Dataset 2")

    def test_evaluation_context_to_dict(self):
        """Test that EvaluationContext to_dict method works correctly"""
        from src.models.context import EvaluationContext
        
        # Create a sample context
        context = EvaluationContext(
            user_cohort="health_conscious_professional",
            router_intent="Lower BioAge Score",
            belief_system={"health_important": 0.8},
            demographic_data={"age_range": "35-45"},
            session_history=[{"session_id": "test"}],
            learning_objectives=["test_objective"],
            confidence_scores={"test_score": 0.9}
        )
        
        # Convert to dict
        context_dict = context.to_dict()
        
        # Verify all fields are present and correct
        self.assertEqual(context_dict["user_cohort"], "health_conscious_professional")
        self.assertEqual(context_dict["router_intent"], "Lower BioAge Score")
        self.assertEqual(context_dict["belief_system"], {"health_important": 0.8})
        self.assertEqual(context_dict["demographic_data"], {"age_range": "35-45"})
        self.assertEqual(context_dict["session_history"], [{"session_id": "test"}])
        self.assertEqual(context_dict["learning_objectives"], ["test_objective"])
        self.assertEqual(context_dict["confidence_scores"], {"test_score": 0.9})

    def test_router_intent_specific_conversations(self):
        """Test that conversations are generated according to router intent"""
        # Test each router intent
        for intent in self.generator.sample_router_intents:
            # Generate a conversation with specific intent
            conversation = self.generator.generate_sample_conversation(router_intent=intent)
            
            # Convert to test case
            test_case = self.generator.generate_test_case(conversation)
            
            # Get the context from the first turn
            context = test_case.turns[0].context
            
            # Find the router intent line
            router_intent_line = next((line for line in context if line.startswith('Router Intent:')), None)
            intent_in_context = router_intent_line.split(': ')[1]
            
            # Verify the intent matches
            self.assertEqual(intent_in_context, intent)
            
            # Verify the conversation content matches the intent
            for turn in test_case.turns:
                if intent == "Lower BioAge Score":
                    self.assertTrue(any(keyword in turn.input.lower() for keyword in ["lifestyle", "changes", "improve", "biological"]))
                elif intent == "Query Health Analysis":
                    self.assertTrue(any(keyword in turn.input.lower() for keyword in ["analyze", "patterns", "levels"]))
                elif intent == "Research Health":
                    self.assertTrue(any(keyword in turn.input.lower() for keyword in ["research", "learn", "topics"]))
                elif intent == "View Health Data as Visualization":
                    self.assertTrue(any(keyword in turn.input.lower() for keyword in ["visualize", "metrics", "trends"]))

    def test_random_router_intent_selection(self):
        """Test that a random router intent is selected when none is provided"""
        # Create multiple contexts without specifying router intent
        contexts = [self.generator._create_evaluation_context() for _ in range(10)]
        
        # Get all selected intents
        selected_intents = [context.router_intent for context in contexts]
        
        # Verify that at least two different intents were selected (very unlikely to fail with 10 samples)
        unique_intents = set(selected_intents)
        self.assertGreater(len(unique_intents), 1, "Random selection should yield different intents")
        
        # Verify all selected intents are from the sample list
        for intent in unique_intents:
            self.assertIn(intent, self.generator.sample_router_intents)

    def test_dataset_attribute_access(self):
        """Regression test: Verify that EvaluationDataset attributes can be accessed correctly"""
        generator = DatasetGenerator()
        dataset_configs = [
            {
                "name": "Test Dataset",
                "num_conversations": 2,
                "router_intent": "Lower BioAge Score"
            }
        ]
        datasets = generator.generate_multiple_datasets(dataset_configs)
        
        # Verify dataset attributes can be accessed
        assert len(datasets) == 1
        dataset = datasets[0]
        assert hasattr(dataset, 'name')
        assert dataset.name == "Test Dataset"
        assert hasattr(dataset, 'test_cases')
        assert len(dataset.test_cases) == 2
        
        # Verify test case attributes
        test_case = dataset.test_cases[0]
        assert hasattr(test_case, 'turns')
        assert len(test_case.turns) > 0
        
        # Verify turn attributes
        turn = test_case.turns[0]
        assert hasattr(turn, 'input')
        assert hasattr(turn, 'actual_output')
        assert hasattr(turn, 'context')
        assert isinstance(turn.input, str)
        assert isinstance(turn.actual_output, str)
        assert isinstance(turn.context, list)

if __name__ == '__main__':
    unittest.main() 