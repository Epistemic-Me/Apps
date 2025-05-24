from typing import Dict

def generate_agent_card(agent_def: dict, base_url: str) -> dict:
    """
    Map Bedrock agent metadata and skills to A2A Agent Card JSON.
    """
    agent = agent_def.get("agent", {})
    skills = agent_def.get("skills", [])
    card = {
        "@context": "https://a2a.org/agent-card/v1",
        "id": f"{base_url}/.well-known/agent.json",
        "name": agent.get("name"),
        "description": agent.get("description"),
        "publisher": agent.get("createdBy"),
        "skills": [
            {
                "id": skill.get("actionGroupId"),
                "name": skill.get("name"),
                "description": skill.get("description"),
            } for skill in skills
        ],
        "endpoints": {
            "tasks": f"{base_url}/tasks"
        },
        "metadata": {
            "bedrock_agent_id": agent.get("agentId"),
            "version": agent.get("agentVersion"),
        }
    }
    return card 