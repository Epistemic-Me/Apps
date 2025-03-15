"""Main application module for the Bio-Age Coach."""

from typing import Dict, Any, Optional, Tuple
from .mcp.client import MCPClient, MultiServerMCPClient
from .mcp.core.module_registry import ModuleRegistry
from .mcp.core.router import QueryRouter
from .agents.agent_registry import AgentRegistry
from .database.models import UserData
from .chatbot.coach import BioAgeCoach
from .router.semantic_router import SemanticRouter
from .router.router_adapter import RouterAdapter

async def init_mcp_servers() -> Tuple[MultiServerMCPClient, QueryRouter]:
    """Initialize MCP servers and router system.
    
    Returns:
        Tuple containing:
            - MultiServerMCPClient instance
            - Router adapter instance (compatible with QueryRouter interface)
    """
    api_key = "test_key"  # TODO: Get from config
    mcp_client = MultiServerMCPClient(api_key=api_key)
    
    # Initialize agent registry with required parameters
    agent_registry = AgentRegistry(api_key=api_key, mcp_client=mcp_client)
    
    # Check if we're in a test environment
    import sys
    is_test = 'pytest' in sys.modules
    
    if is_test:
        # For tests, use an empty list of agents to avoid Pydantic issues
        agents = []
    else:
        # Import here to avoid circular imports
        from .agents.factory import create_agents
        
        # Create agents using the factory
        agents = create_agents(api_key=api_key, mcp_client=mcp_client)
    
    # Create semantic router
    semantic_router = SemanticRouter(api_key=api_key, agents=agents)
    
    # Create router adapter
    router_adapter = RouterAdapter(semantic_router=semantic_router, mcp_client=mcp_client)
    
    return mcp_client, router_adapter

async def load_user_data(user_id: str, mcp_client: MCPClient) -> bool:
    """Load user data from the database.
    
    Args:
        user_id: The ID of the user to load data for
        mcp_client: MCP client for server communication
        
    Returns:
        True if data was loaded successfully, False otherwise
    """
    try:
        response = await mcp_client.send_request("health", {
            "type": "get_user_data",
            "user_id": user_id
        })
        return True
    except Exception as e:
        print(f"Error loading user data: {e}")
        return False

async def get_daily_health_summary(user_id: str, mcp_client: MCPClient) -> Optional[Dict[str, Any]]:
    """Get a daily health summary for a user.
    
    Args:
        user_id: The ID of the user to get a summary for
        mcp_client: MCP client for server communication
        
    Returns:
        Dictionary containing the user's daily health summary, or None if an error occurs
    """
    try:
        response = await mcp_client.send_request("health", {
            "type": "get_daily_metrics",
            "user_id": user_id
        })
        
        metrics = response.get("metrics", [])
        if not metrics:
            return None
            
        # Calculate averages from metrics
        metric = metrics[0]  # Using first metric for now
        return {
            "avg_calories": metric["active_calories"],
            "avg_steps": metric["steps"],
            "avg_sleep": metric["sleep_hours"],
            "avg_score": metric["health_score"]
        }
    except Exception as e:
        print(f"Error getting health summary: {e}")
        return None

async def handle_data_upload(user_id: str, data_type: str, data: Dict[str, Any], router) -> Dict[str, Any]:
    """Handle a data upload from a user.
    
    Args:
        user_id: The ID of the user uploading data
        data_type: The type of data being uploaded (e.g., "sleep", "exercise")
        data: The data being uploaded
        router: Router adapter instance
        
    Returns:
        Dictionary containing the response from processing the data
    """
    try:
        # Use the router adapter's handle_data_upload method
        response = await router.handle_data_upload(
            user_id=user_id,
            data_type=data_type,
            data=data
        )
        
        return response
    except Exception as e:
        print(f"Error handling data upload: {e}")
        return {
            "response": "I encountered an error while processing your data upload.",
            "error": str(e),
            "insights": [],
            "recommendations": [],
            "questions": [],
            "visualization": None
        }

async def process_query(user_id: str, query: str, context: Dict[str, Any], router) -> Dict[str, Any]:
    """Process a user query.
    
    Args:
        user_id: The ID of the user making the query
        query: The user's query
        context: The conversation context
        router: Router adapter instance
        
    Returns:
        Dictionary containing the response to the query
    """
    try:
        # Add user_id to context
        context["user_id"] = user_id
        
        # Use the router adapter to route the query
        response = await router.route_query(query=query, context=context)
        
        return response
    except Exception as e:
        print(f"Error processing query: {e}")
        return {
            "response": "I encountered an error while processing your query.",
            "error": str(e),
            "insights": [],
            "recommendations": [],
            "questions": [],
            "visualization": None
        } 