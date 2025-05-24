import argparse
import json
import logging
import sys
import traceback
from threading import Thread
from time import sleep
from bedrock_a2a_loop.introspection import get_agent_definition, get_agent_version_for_alias
from bedrock_a2a_loop.card_generator import generate_agent_card
from bedrock_a2a_loop.simulator import simulate_conversation, simulate_health_conversations_with_deepeval
from bedrock_a2a_loop.storage import save_conversations
from bedrock_a2a_loop.evaluator import evaluate_conversations, suggest_agent_update_llm
from bedrock_a2a_loop.diff import diff_cards
from bedrock_a2a_loop.redeploy import update_agent_and_alias
import os
import re
import types
from deepdiff import DeepDiff
import boto3

# --- Flask server factory for dynamic card ---
def create_app(card):
    from flask import Flask, jsonify, request, Response
    import time
    import traceback
    app = Flask(__name__)

    @app.route("/.well-known/agent.json")
    def agent_json():
        return jsonify(card)
    
    @app.route("/tasks/sendSubscribe", methods=["POST"])
    def send_subscribe():
        try:
            print("Received /tasks/sendSubscribe POST:", request.data)
            data = request.get_json(force=True, silent=True) or {}
            user_input = data.get("input", "")
            def event_stream():
                # Simulate agent response as SSE
                yield f"event: message\ndata: Echo: {user_input}\n\n"
                time.sleep(0.1)
            return Response(event_stream(), mimetype="text/event-stream")
        except Exception as e:
            print("Error in /tasks/sendSubscribe:", e)
            traceback.print_exc()
            return jsonify({"error": str(e)}), 500
    return app

def conversational_testcases_to_json(conversations):
    """Convert a list of ConversationalTestCase objects to a JSON-serializable list of conversations (list of turns as dicts)."""
    result = []
    for convo in conversations:
        turns = []
        for turn in getattr(convo, 'turns', []):
            ctx = getattr(turn, "context", None)
            # Ensure context is always a non-empty list of strings
            if not ctx:
                ctx = [""]
            elif isinstance(ctx, str):
                ctx = [ctx]
            turns.append({
                "user_input": getattr(turn, "input", None),
                "agent_response": getattr(turn, "actual_output", None),
                "context": ctx
            })
        result.append(turns)
    return result

def json_to_conversational_testcases(conversations_json):
    """Convert a list of conversations (list of turns as dicts) to DeepEval ConversationalTestCase objects."""
    try:
        from deepeval.test_case.conversational_test_case import ConversationalTestCase
        from deepeval.test_case.llm_test_case import LLMTestCase
    except ImportError:
        raise RuntimeError("DeepEval is not installed.")
    result = []
    for convo in conversations_json:
        turns = []
        for turn in convo:
            context = turn.get("context")
            # Ensure context is always a non-empty list of strings
            if not context:
                context = [""]
            elif isinstance(context, str):
                context = [context]
            turns.append(LLMTestCase(input=turn["user_input"], actual_output=turn["agent_response"], context=context))
        result.append(ConversationalTestCase(turns=turns))
    return result

def color_diff(old, new, diff):
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RESET = '\033[0m'
    output = []
    # Show changed values
    if 'values_changed' in diff:
        for change in diff['values_changed']:
            path = change.path()
            output.append(f"{YELLOW}Changed {path}:{RESET}")
            output.append(f"  {RED}- {change.t1}{RESET}")
            output.append(f"  {GREEN}+ {change.t2}{RESET}")
    # Show added items
    if 'dictionary_item_added' in diff:
        for item in diff['dictionary_item_added']:
            path = item.path()
            value = item.t2
            output.append(f"{GREEN}Added {path}: {value}{RESET}")
    # Show removed items
    if 'dictionary_item_removed' in diff:
        for item in diff['dictionary_item_removed']:
            path = item.path()
            value = item.t1
            output.append(f"{RED}Removed {path}: {value}{RESET}")
    if not output:
        output.append(f"{YELLOW}No changes detected.{RESET}")
    return '\n'.join(output)

def ensure_context_on_conversational_testcases(conversations):
    for convo in conversations:
        for turn in getattr(convo, 'turns', []):
            ctx = getattr(turn, "context", None)
            if not ctx:
                turn.context = [""]
            elif isinstance(ctx, str):
                turn.context = [ctx]
    return conversations

def ensure_agent_alias(agent_id, alias, region=None):
    client = boto3.client("bedrock-agent", region_name=region)
    # Check if alias exists
    resp = client.list_agent_aliases(agentId=agent_id)
    for a in resp.get("agentAliasSummaries", []):
        if a.get("agentAliasId") == alias or a.get("agentAliasName") == alias:
            logging.info(f"Alias '{alias}' already exists for agent {agent_id}.")
            return
    # Alias does not exist, create it
    # Try to get the latest published version, else use DRAFT
    agent_resp = client.get_agent(agentId=agent_id)
    version = agent_resp.get("latestAgentVersion")
    if not version or version == "DRAFT":
        raise RuntimeError(
            f"No published version found for agent {agent_id}. "
            "You must publish a version before creating an alias."
        )
    try:
        client.create_agent_alias(
            agentId=agent_id,
            agentAliasName=alias,
            routingConfiguration=[
                {
                    "agentVersion": version
                }
            ]
        )
        logging.info(f"Created alias '{alias}' for agent {agent_id}, pointing to version {version}.")
    except Exception as e:
        logging.error(f"Failed to create alias '{alias}' for agent {agent_id}: {e}")
        raise

def main():
    parser = argparse.ArgumentParser(description="Run A2A → DeepEval → redeploy pipeline.")
    parser.add_argument("--agent-id", type=str, required=True, help="Bedrock Agent ID")
    parser.add_argument("--base-url", type=str, required=True, help="Base URL for A2A card (e.g. https://agents.example.com)")
    parser.add_argument("--alias", type=str, default="staging", help="Alias name for redeployment (e.g. staging, prod)")
    parser.add_argument("--messages-file", type=str, help="Path to JSON file with user messages")
    parser.add_argument("--old-card-file", type=str, help="Path to existing agent.json for diff")
    parser.add_argument("--deepeval-sim", action="store_true", help="Use DeepEval ConversationSimulator for health conversations")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    try:
        logging.info("Fetching agent definition...")
        agent_def = get_agent_definition(args.agent_id)
        logging.info("Agent definition fetched.")
    except Exception as e:
        logging.error(f"Failed to fetch agent definition: {e}")
        traceback.print_exc()
        sys.exit(1)

    try:
        logging.info("Generating A2A Agent Card...")
        new_card = generate_agent_card(agent_def, args.base_url)
        with open("agent.json", "w") as f:
            json.dump(new_card, f, indent=2)
        logging.info("Agent card written to agent.json.")
    except Exception as e:
        logging.error(f"Failed to generate/write agent card: {e}")
        traceback.print_exc()
        sys.exit(1)

    try:
        logging.info("Launching Flask server in background...")
        app = create_app(new_card)
        server_thread = Thread(target=app.run, kwargs={"host": "0.0.0.0", "port": 8000}, daemon=True)
        server_thread.start()
        sleep(2)  # Give server time to start
        logging.info("Flask server started on port 8000.")
    except Exception as e:
        logging.error(f"Failed to launch Flask server: {e}")
        traceback.print_exc()
        sys.exit(1)

    try:
        # Ensure the alias exists for the agent
        aws_region = os.environ.get("AWS_REGION")
        ensure_agent_alias(args.agent_id, args.alias, region=aws_region)

        if args.deepeval_sim:
            logging.info("Simulating health conversations with DeepEval ConversationSimulator...")
            conversations = simulate_health_conversations_with_deepeval(
                args.base_url,
                agent_id=args.agent_id,
                agent_alias=args.alias,
                aws_region=aws_region
            )
            conversations = ensure_context_on_conversational_testcases(conversations)
            # Convert to JSON-serializable format for saving
            conversations_json = conversational_testcases_to_json(conversations)
            save_conversations(conversations_json, local_path="conversation_records.json")
            logging.info(f"Simulated {len(conversations)} conversations, saved to conversation_records.json.")
        else:
            # Try to load conversation_records.json if it exists
            if os.path.exists("conversation_records.json"):
                logging.info("Loading existing conversation_records.json file...")
                with open("conversation_records.json") as f:
                    conversations_json = json.load(f)
                logging.info(f"Loaded {len(conversations_json)} conversations from conversation_records.json.")
                conversations = json_to_conversational_testcases(conversations_json)
            elif args.messages_file:
                with open(args.messages_file) as f:
                    messages = json.load(f)
                logging.info(f"Loaded {len(messages)} messages from {args.messages_file}.")
                # Simulate a single conversation from the messages
                turns = simulate_conversation(args.base_url, messages)
                conversations_json = [turns]
                save_conversations(conversations_json, local_path="conversation_records.json")
                conversations = json_to_conversational_testcases(conversations_json)
                logging.info(f"Conversation records saved to conversation_records.json.")
            else:
                messages = ["Hello", "What can you do?"]
                logging.info("Using default messages.")
                turns = simulate_conversation(args.base_url, messages)
                conversations_json = [turns]
                save_conversations(conversations_json, local_path="conversation_records.json")
                conversations = json_to_conversational_testcases(conversations_json)
                logging.info(f"Conversation records saved to conversation_records.json.")
    except Exception as e:
        logging.error(f"Failed to simulate conversation: {e}")
        traceback.print_exc()
        sys.exit(1)

    try:
        logging.info("Evaluating conversations with DeepEval...")
        results = evaluate_conversations(conversations, metrics=["AnswerRelevancyMetric", "FaithfulnessMetric"])
        logging.info(f"Evaluation results: {json.dumps(results, indent=2)}")

        # --- LLM-based agent update suggestion ---
        old_instruction = agent_def["agent"].get("instruction") or ""
        # Ensure both cards have the instruction field
        if "instruction" not in new_card:
            new_card["instruction"] = old_instruction
        suggested_instruction = None
        # Use the first case's scores and reasons as a simple example (could be averaged or more sophisticated)
        if results["cases"]:
            scores = results["cases"][0]["scores"]
            reasons = results["cases"][0]["reasons"]
            new_instruction = suggest_agent_update_llm(old_instruction, scores, reasons)
            suggested_instruction = new_instruction
            logging.info(f"Suggested new instruction:\n{new_instruction}")
            # Create a new agent card with the updated instruction
            new_card_suggested = dict(new_card)
            new_card_suggested["instruction"] = new_instruction
            # Diff the new suggested card with the old card
            diff = DeepDiff(new_card, new_card_suggested, view='tree')
            logging.info(f"Agent card diff (suggested update):\n{diff.pretty()}")
            # Debug print of the raw diff object
            print("\n\033[1m[DEBUG] Raw DeepDiff object (repr):\033[0m")
            print(repr(diff))
            print("\n\033[1m[DEBUG] Raw DeepDiff object (str):\033[0m")
            print(str(diff))
            # Print colorized diff to terminal (stdout)
            print("\n\033[1mAgent card diff (colorized):\033[0m")
            print(color_diff(new_card, new_card_suggested, diff))
        else:
            logging.warning("No evaluation cases found for agent update suggestion.")
    except Exception as e:
        logging.error(f"Failed to evaluate conversations: {e}")
        traceback.print_exc()
        sys.exit(1)

    if args.old_card_file:
        try:
            with open(args.old_card_file) as f:
                old_card = json.load(f)
            diff = diff_cards(old_card, new_card)
            logging.info(f"Card diff:\n{diff}")
        except Exception as e:
            logging.error(f"Failed to diff cards: {e}")
            traceback.print_exc()

    try:
        logging.info("Redeploying updated agent instructions via Bedrock...")
        # Use the suggested instruction if available, otherwise fall back to the original
        instructions = suggested_instruction if suggested_instruction is not None else (agent_def["agent"].get("instruction") or "")
        if not instructions:
            raise ValueError("No instructions found in agent definition or suggested by LLM.")
        new_version = update_agent_and_alias(args.agent_id, args.alias, instructions)
        logging.info(f"Agent {args.agent_id} updated. Alias '{args.alias}' now points to version {new_version}.")
    except Exception as e:
        logging.error(f"Failed to redeploy agent: {e}")
        traceback.print_exc()
        sys.exit(1)

def test_color_diff():
    old = {
        "name": "AgentX",
        "instruction": "Be helpful.",
        "version": 1,
        "features": ["a", "b"]
    }
    new = {
        "name": "AgentX",
        "instruction": "Be extremely helpful and evidence-based.",
        "version": 2,
        "features": ["a", "b", "c"],
        "new_field": "added!"
    }
    diff = DeepDiff(old, new, view='tree')
    print("\n\033[1mTest: Agent card diff (colorized):\033[0m")
    print(color_diff(old, new, diff))

if __name__ == "__main__":
    import sys
    if "--test-diff" in sys.argv:
        test_color_diff()
    else:
        main() 