from typing import List, Dict
import asyncio
import os
import openai

try:
    from deepeval.metrics import ConversationalGEval
    from deepeval.test_case.conversational_test_case import ConversationalTestCase
    from deepeval.test_case.llm_test_case import LLMTestCase
    from deepeval.test_case.llm_test_case import LLMTestCaseParams
    DEEPEVAL_AVAILABLE = True
except ImportError:
    DEEPEVAL_AVAILABLE = False

def evaluate_conversations(conversations: list, metrics: list = None) -> dict:
    """
    Evaluate a list of DeepEval ConversationalTestCase objects using DeepEval metrics (custom ConversationalGEval).
    Returns a dict with per-metric scores for each conversation.
    Input must be a list of ConversationalTestCase objects.
    """
    # Import DeepEval types
    try:
        from deepeval.test_case.conversational_test_case import ConversationalTestCase
    except ImportError:
        raise RuntimeError("DeepEval is not installed.")

    if not conversations:
        return {"summary": "No conversations to evaluate", "metrics": metrics, "cases": []}

    if not isinstance(conversations, list) or not isinstance(conversations[0], ConversationalTestCase):
        raise TypeError("evaluate_conversations expects a list of ConversationalTestCase objects.")

    if not DEEPEVAL_AVAILABLE:
        # Fallback to mock
        test_cases = []
        for convo in conversations:
            test_cases.append({"turns": convo})
        results = {"summary": "Evaluation run (mocked)", "metrics": metrics, "cases": test_cases}
        return results

    # Define custom metrics (mirroring services/evaluation.py)
    custom_metrics = [
        ConversationalGEval(
            name="User Identification",
            evaluation_steps=[
                "1. Check if the user's cohort membership is clear and consistent",
                "2. Identify specific characteristics that place them in their cohort",
                "3. Look for unique identifiers in responses that confirm cohort alignment",
                "4. Assess confidence in user's demographic and psychographic profile"
            ],
            evaluation_params=[
                LLMTestCaseParams.INPUT,
                LLMTestCaseParams.ACTUAL_OUTPUT,
                LLMTestCaseParams.CONTEXT
            ],
            model='gpt-4o',
            threshold=0.7,
            async_mode=True,
            verbose_mode=False
        ),
        ConversationalGEval(
            name="Belief Evidencing",
            evaluation_steps=[
                "1. Check if user shares personal experiences supporting their beliefs",
                "2. Assess if experiences are specific and detailed enough to be credible",
                "3. Verify clear connection between experiences and stated beliefs",
                "4. Evaluate consistency of evidencing patterns across different beliefs"
            ],
            evaluation_params=[
                LLMTestCaseParams.INPUT,
                LLMTestCaseParams.ACTUAL_OUTPUT,
                LLMTestCaseParams.CONTEXT
            ],
            model='gpt-4o',
            threshold=0.7,
            async_mode=True,
            verbose_mode=False
        ),
        ConversationalGEval(
            name="Belief Verification",
            evaluation_steps=[
                "1. Check if output aligns with user's existing belief system",
                "2. Verify new concepts are introduced building on existing beliefs",
                "3. Identify potential cognitive dissonance and how it's addressed",
                "4. Assess evidence suggesting user will find output credible"
            ],
            evaluation_params=[
                LLMTestCaseParams.INPUT,
                LLMTestCaseParams.ACTUAL_OUTPUT,
                LLMTestCaseParams.CONTEXT
            ],
            model='gpt-4o',
            threshold=0.7,
            async_mode=True,
            verbose_mode=False
        )
    ]

    async def eval_one(test_case):
        scores = {}
        reasons = {}
        for metric in custom_metrics:
            await metric.a_measure(test_case)
            scores[metric.name] = metric.score
            reasons[metric.name] = getattr(metric, 'reason', None)
        return scores, reasons

    async def eval_all():
        results = []
        for test_case in conversations:
            scores, reasons = await eval_one(test_case)
            results.append({
                "turns": [
                    {
                        "user_input": getattr(turn, "input", None),
                        "agent_response": getattr(turn, "actual_output", None),
                        "context": getattr(turn, "context", None)
                    } for turn in getattr(test_case, 'turns', [])
                ],
                "scores": scores,
                "reasons": reasons
            })
        return results

    loop = asyncio.get_event_loop()
    cases = loop.run_until_complete(eval_all())
    return {
        "summary": "Evaluation run (DeepEval)",
        "metrics": [m.name for m in custom_metrics],
        "cases": cases
    }

def suggest_agent_update_llm(old_instruction: str, scores: dict, reasons: dict) -> str:
    """
    Use an LLM (OpenAI GPT-4o) to suggest an improved agent instruction based on scores and reasons.
    """
    openai.api_key = os.getenv("OPENAI_API_KEY")
    prompt = f"""
You are an expert prompt engineer for health-focused AI agents.

Here is the agent's current instruction:
---
{old_instruction}
---

Here are the latest evaluation scores and reasons for the agent's conversations:
Scores: {scores}
Reasons: {reasons}

Based on the above, suggest a revised instruction for the agent that will improve its performance on the evaluated metrics. Be specific and actionable. Only output the new instruction, no commentary.
"""
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=512,
        temperature=0.3
    )
    new_instruction = response.choices[0].message.content.strip()
    return new_instruction

# --- Unit Test ---
def _test_evaluate_conversations():
    """Unit test for evaluate_conversations (mock and DeepEval)."""
    records = [
        {"user_input": "Hello, what is hypertension?", "agent_response": "Hypertension is high blood pressure."},
        {"user_input": "How can I manage it?", "agent_response": "Lifestyle changes and medication can help."}
    ]
    print("Testing evaluate_conversations...")
    result = evaluate_conversations(records)
    print("Result:", result)
    assert "cases" in result
    assert len(result["cases"]) == 2
    for case in result["cases"]:
        print("Scores:", case["scores"])
        print("Reasons:", case["reasons"])
    print("evaluate_conversations test passed.")

if __name__ == "__main__":
    _test_evaluate_conversations() 