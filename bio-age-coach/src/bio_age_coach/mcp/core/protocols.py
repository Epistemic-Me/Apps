"""
Protocol definitions for MCP system.
"""

from typing import Dict, Any, Protocol

class MCPServer(Protocol):
    """Protocol defining the interface for MCP servers."""
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process a request and return response."""
        ...
    
    async def close(self) -> None:
        """Close server connection."""
        ... 