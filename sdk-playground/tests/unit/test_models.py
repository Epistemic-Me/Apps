import pytest
from datetime import datetime
from src.models.base import (
    BeliefSystem,
    SelfModel,
    DialogueInteraction,
    TrainingMetrics,
    EvaluationResult
)

@pytest.fixture
def sample_belief_system():
    return BeliefSystem(
        beliefs={"health_important": 0.9, "exercise_beneficial": 0.8},
        last_updated=datetime.now(),
        entropy=0.3
    )

@pytest.fixture
def sample_self_model(sample_belief_system):
    return SelfModel(
        belief_system=sample_belief_system,
        learning_progress=0.75,
        model_version="1.0.0"
    )

def test_belief_system_creation(sample_belief_system):
    assert isinstance(sample_belief_system, BeliefSystem)
    assert len(sample_belief_system.beliefs) == 2
    assert 0 <= sample_belief_system.entropy <= 1

def test_self_model_creation(sample_self_model):
    assert isinstance(sample_self_model, SelfModel)
    assert isinstance(sample_self_model.belief_system, BeliefSystem)
    assert 0 <= sample_self_model.learning_progress <= 1

def test_dialogue_interaction():
    interaction = DialogueInteraction(
        id="test_1",
        timestamp=datetime.now(),
        coach_message="How do you feel about exercise?",
        user_message="I believe it's important",
        evaluation_score=0.85,
        belief_updates={"exercise_beneficial": 0.1}
    )
    assert isinstance(interaction, DialogueInteraction)
    assert interaction.id == "test_1"
    assert interaction.evaluation_score is not None

def test_training_metrics():
    metrics = TrainingMetrics(
        interaction_id="test_1",
        entropy=0.4,
        learning_progress=0.6,
        timestamp=datetime.now()
    )
    assert isinstance(metrics, TrainingMetrics)
    assert 0 <= metrics.entropy <= 1
    assert 0 <= metrics.learning_progress <= 1

def test_evaluation_result():
    result = EvaluationResult(
        interaction_id="test_1",
        metrics={"accuracy": 0.9, "relevance": 0.85},
        timestamp=datetime.now(),
        confidence_score=0.88
    )
    assert isinstance(result, EvaluationResult)
    assert len(result.metrics) == 2
    assert 0 <= result.confidence_score <= 1 