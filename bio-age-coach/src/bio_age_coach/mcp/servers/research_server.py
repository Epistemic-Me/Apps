"""
Research server implementation for managing research data and insights.
"""

from typing import Dict, Any, List, Optional
import json
import os
from pathlib import Path
from ..core.base import BaseMCPServer
import aiohttp

class ResearchServer(BaseMCPServer):
    """Server for retrieving research insights."""
    
    def __init__(self, api_key: str, data_path: str = "data/research"):
        """Initialize the research server.
        
        Args:
            api_key (str): API key for authentication
            data_path (str): Directory containing research papers
        """
        super().__init__(api_key)
        self.data_path = data_path
        self.papers_dir = Path(data_path)
        self.papers_cache = {}
        self.paper_index = {}
        self.session: Optional[aiohttp.ClientSession] = None
        self.papers_data = {}
        os.makedirs(self.data_path, exist_ok=True)
        
    async def _process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming requests."""
        try:
            request_type = request.get("type", "")
            
            if request_type == "get_insights":
                query = request.get("query", "")
                insights = await self.get_insights(query)
                return {"insights": insights}
            elif request_type == "get_papers":
                query = request.get("query", "")
                papers = await self.get_papers(query)
                return {"papers": papers}
            elif request_type == "initialize_data":
                await self.initialize_data(request.get("data", {}))
                return {"status": "success"}
            else:
                return {"error": f"Unknown request type: {request_type}"}
        except Exception as e:
            print(f"Error processing request: {str(e)}")
            return {"error": f"Error processing request: {str(e)}"}
        
    async def get_insights(self, query: str) -> List[Dict[str, Any]]:
        """Get research insights based on a query."""
        try:
            # For now, return a default insight
            return [{
                "source": "default",
                "insight": "Regular exercise has been shown to improve longevity and healthspan.",
                "confidence": 0.8
            }]
        except Exception as e:
            self.logger.error(f"Error getting insights: {str(e)}")
            return []
        
    async def close(self) -> None:
        """Close the server connection."""
        if self.session:
            await self.session.close()
            
    async def initialize_data(self, data: Optional[Dict[str, Any]] = None) -> None:
        """Initialize server data with optional test data."""
        try:
            # Ensure data directory exists
            os.makedirs(self.data_path, exist_ok=True)
            
            # Initialize paper index
            self._initialize_paper_index()
            
            if data:
                # Save test data to file
                config_path = os.path.join(self.data_path, "research_config.json")
                with open(config_path, "w") as f:
                    json.dump(data, f, indent=4)
                    
        except Exception as e:
            self.logger.error(f"Error initializing data: {str(e)}")
            
    def _initialize_paper_index(self):
        """Initialize the paper index from the papers directory."""
        try:
            if not self.papers_dir.exists():
                os.makedirs(self.papers_dir)
                return
                
            # Load paper metadata
            paper_files = list(self.papers_dir.glob("*.json"))
            
            for paper_file in paper_files:
                try:
                    with open(paper_file, 'r') as f:
                        paper_data = json.load(f)
                        self.paper_index[paper_file.stem] = {
                            "title": paper_data.get("title", ""),
                            "abstract": paper_data.get("abstract", ""),
                            "keywords": paper_data.get("keywords", []),
                            "year": paper_data.get("year", ""),
                            "authors": paper_data.get("authors", [])
                        }
                except Exception as e:
                    self.logger.error(f"Error loading paper {paper_file}: {str(e)}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"Error initializing paper index: {str(e)}")
            
    async def get_papers(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get papers matching a query."""
        try:
            # For now, return an empty list
            return []
        except Exception as e:
            self.logger.error(f"Error getting papers: {str(e)}")
            return [] 