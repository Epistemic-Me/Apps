from flask import Flask, jsonify
from .card_generator import generate_agent_card

app = Flask(__name__)

# For demonstration, use a stub agent_def and base_url
agent_def = {
    "agent": {"name": "Demo Agent", "description": "A demo agent.", "createdBy": "demo", "agentId": "demo-id", "agentVersion": "1.0"},
    "skills": []
}
base_url = "http://localhost:5000"

@app.route("/.well-known/agent.json")
def agent_json():
    card = generate_agent_card(agent_def, base_url)
    return jsonify(card)

if __name__ == "__main__":
    app.run(port=5000) 