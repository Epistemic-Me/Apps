import boto3
from typing import Optional

def get_alias_id(agent_id: str, alias_name: str) -> str:
    """
    Return the alias ID for a given alias name.
    """
    client = boto3.client("bedrock-agent")
    aliases = client.list_agent_aliases(agentId=agent_id)["agentAliasSummaries"]
    for a in aliases:
        if a["agentAliasName"] == alias_name:
            return a["agentAliasId"]
    raise ValueError(f"Alias {alias_name} not found for agent {agent_id}")

def update_agent_and_alias(agent_id: str, alias_name: str, new_instruction: str) -> str:
    """
    Update the agent with new instructions, then update the alias to point to the latest version.
    Returns the new version number.
    """
    client = boto3.client("bedrock-agent")
    # Fetch current agent config
    agent = client.get_agent(agentId=agent_id)["agent"]
    update_kwargs = {
        "agentId": agent_id,
        "agentName": agent.get("agentName") or agent.get("name"),
        "agentResourceRoleArn": agent["agentResourceRoleArn"],
        "foundationModel": agent["foundationModel"],
        "instruction": new_instruction,
    }
    if "description" in agent or "agentDescription" in agent:
        update_kwargs["description"] = agent.get("description") or agent.get("agentDescription")
    if "idleSessionTTLInSeconds" in agent:
        update_kwargs["idleSessionTTLInSeconds"] = agent["idleSessionTTLInSeconds"]
    client.update_agent(**update_kwargs)

    # Find the latest version (highest number)
    versions = client.list_agent_versions(agentId=agent_id)["agentVersionSummaries"]
    numeric_versions = [v for v in versions if v["agentVersion"].isdigit()]
    latest_version = max(numeric_versions, key=lambda v: int(v["agentVersion"]))["agentVersion"]

    # Fetch both alias ID and name
    aliases = client.list_agent_aliases(agentId=agent_id)["agentAliasSummaries"]
    alias_id = None
    alias_name_actual = None
    for a in aliases:
        if a["agentAliasName"] == alias_name:
            alias_id = a["agentAliasId"]
            alias_name_actual = a["agentAliasName"]
            break
    if not alias_id or not alias_name_actual:
        raise ValueError(f"Alias {alias_name} not found for agent {agent_id}")

    client.update_agent_alias(
        agentId=agent_id,
        agentAliasId=alias_id,
        agentAliasName=alias_name_actual,
        routingConfiguration=[{"agentVersion": latest_version}]
    )
    return latest_version 