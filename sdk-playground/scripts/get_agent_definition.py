import sys
from bedrock_a2a_loop.introspection import get_agent_definition

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python get_agent_definition.py <agent_id>")
        sys.exit(1)
    agent_id = sys.argv[1]
    agent_def = get_agent_definition(agent_id)
    import json
    print(json.dumps(agent_def, indent=2)) 