from fastapi import APIRouter, Depends, HTTPException
from typing import List
from datetime import datetime

from ..models.base import (
    DialogueInteraction,
    EvaluationResult,
    TrainingMetrics
)
from ..services.evaluation import DialogueEvaluator
from ...config.settings import get_settings, Settings

router = APIRouter()
evaluator = DialogueEvaluator()

@router.post("/evaluate", response_model=EvaluationResult)
async def evaluate_interaction(
    interaction: DialogueInteraction,
    settings: Settings = Depends(get_settings)
):
    """
    Evaluate a single dialogue interaction.
    """
    try:
        result = await evaluator.evaluate_interaction(interaction)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/evaluate/batch", response_model=List[EvaluationResult])
async def evaluate_batch(
    interactions: List[DialogueInteraction],
    settings: Settings = Depends(get_settings)
):
    """
    Evaluate a batch of dialogue interactions.
    """
    if len(interactions) > settings.EVALUATION_BATCH_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Batch size cannot exceed {settings.EVALUATION_BATCH_SIZE}"
        )
    
    try:
        results = await evaluator.batch_evaluate(interactions)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics/{interaction_id}", response_model=TrainingMetrics)
async def get_metrics(
    interaction_id: str,
    settings: Settings = Depends(get_settings)
):
    """
    Get training metrics for a specific interaction.
    """
    # This would typically fetch from a database
    # For now, return mock data
    return TrainingMetrics(
        interaction_id=interaction_id,
        entropy=0.5,
        learning_progress=0.75,
        timestamp=datetime.now()
    ) 