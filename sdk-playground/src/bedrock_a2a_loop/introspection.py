import boto3
from typing import Dict, Optional

def get_agent_version_for_alias(agent_id: str, alias_name: str) -> str:
    """
    Given an agent_id and alias_name, return the numeric agentVersion associated with that alias.
    Raises ValueError if not found.
    """
    client = boto3.client("bedrock-agent")
    aliases = client.list_agent_aliases(agentId=agent_id)["agentAliasSummaries"]
    for a in aliases:
        if a["agentAliasName"] == alias_name:
            return a["agentVersion"]
    raise ValueError(f"Alias {alias_name} not found for agent {agent_id}")

def get_agent_definition(agent_id: str, agent_version: Optional[str] = None) -> dict:
    """
    Fetch agent metadata and action groups from AWS Bedrock using boto3.
    Returns a dict with agent metadata and skills (action groups).
    agent_version: must be a numeric string or 'DRAFT'.
    """
    client = boto3.client("bedrock-agent")
    agent = client.get_agent(agentId=agent_id)["agent"]
    agent_version = agent_version or agent.get("agentVersion", "DRAFT")
    action_groups = client.list_agent_action_groups(agentId=agent_id, agentVersion=agent_version)["actionGroupSummaries"]
    return {
        "agent": agent,
        "skills": action_groups
    } 