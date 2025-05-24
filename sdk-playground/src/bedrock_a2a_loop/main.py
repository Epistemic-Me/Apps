import threading
import time
from bedrock_a2a_loop.introspection import get_agent_definition
from bedrock_a2a_loop.card_generator import generate_agent_card
from bedrock_a2a_loop.server import app as flask_app
from bedrock_a2a_loop.simulator import simulate_conversation
from bedrock_a2a_loop.storage import save_conversations, load_conversations
from bedrock_a2a_loop.evaluator import evaluate_conversations
from bedrock_a2a_loop.diff import diff_cards
from bedrock_a2a_loop.redeploy import update_and_alias

# --- Step 1: Introspect agent ---
agent_id = "demo-id"
base_url = "http://localhost:5000"
agent_def = {
    "agent": {"name": "Demo Agent", "description": "A demo agent.", "createdBy": "demo", "agentId": agent_id, "agentVersion": "1.0"},
    "skills": [
        {"actionGroupId": "skill1", "name": "Skill 1", "description": "First skill."}
    ]
}
# agent_def = get_agent_definition(agent_id)  # Uncomment for real AWS

# --- Step 2: Generate agent card ---
card = generate_agent_card(agent_def, base_url)
print("Generated Agent Card:", card)

# --- Step 3: Launch server in background ---
def run_server():
    flask_app.run(port=5000)
server_thread = threading.Thread(target=run_server, daemon=True)
server_thread.start()
time.sleep(1)  # Wait for server to start

# --- Step 4: Simulate conversation ---
messages = ["Hello", "What can you do?"]
results = [
    {"user_input": m, "agent_response": f"Echo: {m}"} for m in messages
]
# results = simulate_conversation(base_url, messages)  # Uncomment for real endpoint
print("Simulated Conversation:", results)

# --- Step 5: Store conversation ---
local_path = "conversation.json"
save_conversations(results, local_path=local_path)

# --- Step 6: Evaluate conversation ---
metrics = ["accuracy", "relevance"]
eval_results = evaluate_conversations(results, metrics)
print("Evaluation Results:", eval_results)

# --- Step 7: Diff cards ---
old_card = card.copy()
new_card = card.copy()
new_card["description"] = "A new description."
diff = diff_cards(old_card, new_card)
print("Card Diff:\n", diff)

# --- Step 8: Redeploy ---
# update_and_alias(agent_id, "New instructions", "prod")  # Uncomment for real AWS
print("Redeploy step (mocked)") 