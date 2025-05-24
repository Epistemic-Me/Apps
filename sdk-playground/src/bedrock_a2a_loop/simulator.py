import requests
from typing import List, Dict, Optional
import boto3
import uuid
import logging

def simulate_conversation(agent_url: str, messages: List[str]) -> List[Dict]:
    """
    Simulate a conversation with the agent by sending messages to the A2A tasks/sendSubscribe endpoint.
    For local mock, parse the response text directly as SSE.
    """
    results = []
    sse_url = f"{agent_url}/tasks/sendSubscribe"
    for msg in messages:
        response = requests.post(sse_url, json={"input": msg})
        if response.status_code == 200 and response.headers.get("Content-Type", "").startswith("text/event-stream"):
            # Parse the SSE event manually (for mock)
            lines = response.text.splitlines()
            agent_response = ""
            for line in lines:
                if line.startswith("data: "):
                    agent_response = line[len("data: "):]
            results.append({"user_input": msg, "agent_response": agent_response})
        else:
            raise RuntimeError(f"Bad response: {response.status_code} {response.text}")
    return results

# For real SSE endpoints, use this instead:
# from sseclient import SSEClient
# def simulate_conversation(agent_url: str, messages: List[str]) -> List[Dict]:
#     results = []
#     sse_url = f"{agent_url}/tasks/sendSubscribe"
#     for msg in messages:
#         response = requests.post(sse_url, json={"input": msg}, stream=True)
#         client = SSEClient(response)
#         agent_response = ""
#         for event in client.events():
#             if event.event == "message":
#                 data = event.data
#                 agent_response = data  # In real use, parse JSON if needed
#                 break
#         results.append({"user_input": msg, "agent_response": agent_response})
#     return results 

# --- DeepEval Conversation Simulator Integration ---
def simulate_health_conversations_with_deepeval(
    agent_url: str,
    num_conversations: int = 2,
    min_turns: int = 3,
    max_turns: int = 6,
    user_profile_items: Optional[List[str]] = None,
    user_intentions: Optional[List[str]] = None,
    simulator_model: Optional[str] = None,
    async_mode: bool = True,
    agent_id: Optional[str] = None,
    agent_alias: Optional[str] = None,  # can be alias name or id
    aws_region: Optional[str] = None,
) -> list:
    """
    Use DeepEval's ConversationSimulator to generate health-related conversations with the agent.
    Each turn, the agent is called via the A2A endpoint or Bedrock agent runtime if agent_id/alias is provided.
    Returns a list of simulated conversations.
    """
    from deepeval.conversation_simulator import ConversationSimulator
    import httpx
    import functools

    if user_profile_items is None:
        user_profile_items = [
            "sex", "age", "weight", "height", "medical history", "current medications"
        ]
    if user_intentions is None:
        # user_intentions = [
        #     "retrieving reliable, science-based health information",
        #     "asking about disease risk factors",
        #     "inquiring about medication side effects",
        #     "seeking advice on healthy lifestyle changes"
        # ]
        user_intentions = [
            "To onboard as a new user for an AI health coach",
            "share the user's health profile with the coach",
            "share habits about sleep, diet, and exercise",
            "retrieve information about the user's health profile",
            "sync health data from a wearable device",
            "review results of uploaded health data and compare with current habits"
        ]

    convo_simulator = ConversationSimulator(
        user_profile_items=user_profile_items,
        user_intentions=user_intentions,
        simulator_model=simulator_model or "gpt-4o"
    )

    def get_alias_id(agent_id: str, alias: str, region: Optional[str] = None) -> str:
        """
        Given an alias name or id, return the alias id. If alias is already an id, return as is.
        """
        if not agent_id or not alias:
            raise ValueError("Both agent_id and alias are required to fetch alias id.")
        client = boto3.client("bedrock-agent", region_name=region)
        # Try to find alias by name
        resp = client.list_agent_aliases(agentId=agent_id)
        for a in resp.get("agentAliasSummaries", []):
            if a.get("agentAliasId") == alias or a.get("agentAliasName") == alias:
                return a["agentAliasId"]
        raise ValueError(f"Alias '{alias}' not found for agent {agent_id}")

    if agent_id and agent_alias:
        # Use Bedrock agent runtime
        def get_bedrock_response(user_input: str, session_id: str) -> str:
            region = aws_region
            runtime_client = boto3.client("bedrock-agent-runtime", region_name=region)
            alias_id = get_alias_id(agent_id, agent_alias, region)
            try:
                response = runtime_client.invoke_agent(
                    agentId=agent_id,
                    agentAliasId=alias_id,
                    sessionId=session_id,
                    inputText=user_input,
                )
                completion = ""
                for event in response.get("completion", []):
                    if "chunk" in event:
                        completion += event["chunk"]["bytes"].decode()
                return completion
            except Exception as e:
                logging.error(f"Error invoking Bedrock agent: {e}")
                return f"Error: {e}"

        async def model_callback(user_input: str, session_id: str = None) -> str:
            # session_id is required for multi-turn
            if session_id is None:
                session_id = str(uuid.uuid4())
            return get_bedrock_response(user_input, session_id)
    else:
        # Fallback to current SSE logic
        async def model_callback(user_input: str, session_id: str = None) -> str:
            sse_url = f"{agent_url}/tasks/sendSubscribe"
            async with httpx.AsyncClient() as client:
                response = await client.post(sse_url, json={"input": user_input})
                if response.status_code == 200 and response.headers.get("Content-Type", "").startswith("text/event-stream"):
                    lines = response.text.splitlines()
                    for line in lines:
                        if line.startswith("data: "):
                            return line[len("data: ") :]
                return f"Error: {response.status_code}"

    # Patch ConversationSimulator to pass session_id for continuity
    orig_simulate = convo_simulator.simulate
    def simulate_with_session(model_callback, *args, **kwargs):
        session_id = str(uuid.uuid4())
        # Wrap model_callback to always pass session_id
        async def cb_with_session(user_input):
            return await model_callback(user_input, session_id=session_id)
        return orig_simulate(cb_with_session, *args, **kwargs)
    convo_simulator.simulate = functools.partial(simulate_with_session, model_callback)

    convo_simulator.simulate(
        min_turns=min_turns,
        max_turns=max_turns,
        num_conversations=num_conversations
    )
    return convo_simulator.simulated_conversations 