import pytest
from unittest.mock import patch, MagicMock
from bedrock_a2a_loop import introspection, card_generator, simulator, storage, evaluator, diff, redeploy

# Introspection
@patch('boto3.client')
def test_get_agent_definition(mock_boto):
    mock_client = MagicMock()
    mock_client.get_agent.return_value = {"agent": {"name": "TestAgent"}}
    mock_client.list_agent_action_groups.return_value = {"actionGroupSummaries": [{"name": "Skill1"}]}
    mock_boto.return_value = mock_client
    result = introspection.get_agent_definition("agent-id")
    assert result["agent"]["name"] == "TestAgent"
    assert result["skills"][0]["name"] == "Skill1"

# Card Generator
def test_generate_agent_card():
    agent_def = {"agent": {"name": "A", "description": "D", "createdBy": "P", "agentId": "id", "agentVersion": "v"}, "skills": [{"actionGroupId": "s1", "name": "S", "description": "SD"}]}
    card = card_generator.generate_agent_card(agent_def, "http://x")
    assert card["name"] == "A"
    assert card["skills"][0]["id"] == "s1"

# Simulator
@patch('bedrock_a2a_loop.simulator.SSEClient')
@patch('bedrock_a2a_loop.simulator.requests.post')
def test_simulate_conversation(mock_post, mock_sse):
    mock_event = MagicMock()
    mock_event.event = "message"
    mock_event.data = "response"
    mock_sse.return_value.events.return_value = [mock_event]
    mock_post.return_value = MagicMock()
    res = simulator.simulate_conversation("http://x", ["hi"])
    assert res[0]["agent_response"] == "response"

# Storage
@patch('boto3.resource')
def test_save_and_load_conversations_dynamo(mock_resource):
    mock_table = MagicMock()
    mock_resource.return_value.Table.return_value = mock_table
    records = [{"a": 1}]
    storage.save_conversations(records, table_name="t")
    mock_table.put_item.assert_called_with(Item=records[0])
    mock_table.scan.return_value = {"Items": records}
    loaded = storage.load_conversations(table_name="t")
    assert loaded == records

def test_save_and_load_conversations_local(tmp_path):
    records = [{"a": 2}]
    file = tmp_path / "c.json"
    storage.save_conversations(records, local_path=str(file))
    loaded = storage.load_conversations(local_path=str(file))
    assert loaded == records

# Evaluator
def test_evaluate_conversations():
    records = [{"user_input": "hi", "agent_response": "hello"}]
    metrics = ["accuracy"]
    res = evaluator.evaluate_conversations(records, metrics)
    assert "summary" in res

# Diff
def test_diff_cards():
    old = {"a": 1}
    new = {"a": 2}
    out = diff.diff_cards(old, new)
    assert "a" in out

# Redeploy
@patch('boto3.client')
def test_update_and_alias(mock_boto):
    mock_client = MagicMock()
    mock_boto.return_value = mock_client
    redeploy.update_and_alias("id", "instr", "alias")
    mock_client.update_agent.assert_called()
    mock_client.create_agent_alias.assert_called()

def test_simulate_health_conversations_with_deepeval(monkeypatch):
    # Patch ConversationSimulator to avoid real LLM calls
    class DummyConvoSim:
        def __init__(self, *a, **k):
            self.simulated_conversations = [
                [
                    {"user_input": "What is a healthy weight?", "agent_response": "Echo: What is a healthy weight?"},
                    {"user_input": "What are risk factors for diabetes?", "agent_response": "Echo: What are risk factors for diabetes?"}
                ]
            ]
        def simulate(self, model_callback, min_turns, max_turns, num_conversations):
            # Call the callback to ensure it works
            assert callable(model_callback)
            assert isinstance(model_callback("Test input"), str)

    monkeypatch.setattr("deepeval.conversation_simulator.ConversationSimulator", DummyConvoSim)

    # Patch requests.post to simulate agent endpoint
    def fake_post(url, json):
        class Resp:
            status_code = 200
            headers = {"Content-Type": "text/event-stream"}
            text = "event: message\ndata: Echo: {}\n\n".format(json["input"])
        return Resp()
    monkeypatch.setattr(simulator.requests, "post", fake_post)

    convos = simulator.simulate_health_conversations_with_deepeval("http://fake-agent")
    assert isinstance(convos, list)
    assert isinstance(convos[0], list)
    assert "user_input" in convos[0][0]
    assert "agent_response" in convos[0][0]

def test_simulate_conversation(monkeypatch):
    # Patch requests.post to simulate agent endpoint
    def fake_post(url, json):
        class Resp:
            status_code = 200
            headers = {"Content-Type": "text/event-stream"}
            text = "event: message\ndata: Echo: {}\n\n".format(json["input"])
        return Resp()
    monkeypatch.setattr(simulator.requests, "post", fake_post)

    res = simulator.simulate_conversation("http://x", ["hi"])
    assert res[0]["agent_response"] == "Echo: hi" 