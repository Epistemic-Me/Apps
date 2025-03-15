# Semantic Router for Bio Age Coach

This module implements a semantic router for the Bio Age Coach system, which routes user queries to the appropriate agent based on semantic similarity and observation contexts.

## Overview

The semantic router is designed to replace the rule-based `QueryRouter` with a more flexible and powerful semantic routing system. It uses embeddings to match user queries with agent capabilities and leverages observation contexts to provide personalized responses based on user data.

## Components

### SemanticRouter

The `SemanticRouter` class is the core component of the routing system. It:

- Uses embeddings to match user queries with agent capabilities
- Maintains a history of routing decisions
- Supports data uploads and observation contexts
- Combines responses from multiple agents when appropriate

### RouterAdapter

The `RouterAdapter` class provides backward compatibility with the existing `QueryRouter` interface. It:

- Wraps the `SemanticRouter` to maintain the same interface
- Formats responses to match the expected format
- Provides methods for updating and clearing context
- Handles data uploads

### ObservationContext

The `ObservationContext` class represents the schema for how agents interpret and analyze user data. It:

- Stores raw and processed data
- Maps data to enumerated states (current and goal)
- Calculates relevancy scores for queries
- Generates insights, recommendations, and questions
- Provides visualization data

Specialized observation contexts like `SleepObservationContext` and `ExerciseObservationContext` provide domain-specific functionality.

### Factory Functions

The module provides factory functions for creating router components:

- `create_semantic_router`: Creates a semantic router instance
- `create_router_adapter`: Creates a router adapter instance
- `initialize_router_system`: Initializes the complete router system

## Usage

### Basic Usage

```python
from bio_age_coach.router import initialize_router_system

# Initialize the router system
router_system = await initialize_router_system(api_key="your_api_key")

# Get the router adapter
router_adapter = router_system["router_adapter"]

# Route a query
response = await router_adapter.route_query(
    query="How is my sleep quality?",
    context={"user_id": "user123"}
)
```

### Handling Data Uploads

```python
# Handle a data upload
response = await router_adapter.handle_data_upload(
    user_id="user123",
    data_type="sleep",
    data=sleep_data
)
```

### Managing Context

```python
# Update context
router_adapter.update_context(
    user_id="user123",
    context_update={"new_key": "new_value"}
)

# Clear context
router_adapter.clear_context(user_id="user123")
```

## Integration with Agents

Agents need to support the following methods to work with the semantic router:

- `create_observation_context`: Creates an observation context for a specific data type
- `can_handle`: Determines if the agent can handle a query
- `process`: Processes a query and returns a response

## Example

See the `examples/semantic_router_example.py` script for a complete example of how to use the semantic router with observation contexts. 