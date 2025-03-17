# Bio-Age Coach Implementation Plan (Updated with MCP Integration)

## Overview
This plan outlines the integration of MCP servers into our existing Bio-Age Coach application. The update focuses on modularizing our data handling into three distinct MCP servers while maintaining and enhancing our current functionality.

## Part 1: Completed Tasks ✅

### 1. Project Setup ✅
- [x] Create basic directory structure
- [x] Set up virtual environment
- [x] Install required packages
- [x] Configure environment variables

```bash
# Setup commands (already completed)
cd Apps/bio-age-coach
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Data Model Implementation ✅
- [x] Define biomarker schema with multiple categories
- [x] Create comprehensive biomarker datasets
- [x] Implement health data categorization system
- [x] Create test cases for evaluation

Key files:
1. `data/biomarkers.json` - Biomarker definitions across six categories
2. `data/protocols.json` - Protocols and recommendations for improving biomarkers

### 3. Chatbot Core Implementation ✅
- [x] Create conversation flow system
- [x] Define prompt templates for different conversation stages
- [x] Implement biomarker analysis logic
- [x] Implement recommendation engine
- [x] Add data completeness assessment

Key components:
- `src/chatbot/coach.py` - Main chatbot logic with BioAgeCoach class
- `src/chatbot/prompts.py` - System prompts and templates for different coaching scenarios

### 4. UI Implementation ✅
- [x] Create Streamlit application
- [x] Implement chat interface
- [x] Add category-based biomarker input forms
- [x] Implement results display
- [x] Add data completeness visualizations (progress bars and radar chart)

### 5. Evaluation Framework ✅
- [x] Create test cases for different coach capabilities
- [x] Implement evaluation metrics (AnswerRelevancyMetric)
- [x] Run initial evaluation
- [x] Enable Confident AI integration

### 6. Documentation and Deployment ✅
- [x] Create comprehensive README
- [x] Document setup and usage instructions
- [x] Outline development roadmap
- [x] Initial deployment and testing

## Part 2: MCP Integration (Current Focus) 🔄

### 7. Project Structure Update ✅
```
bio-age-coach/
├── app.py                 # Main Streamlit app
├── requirements.txt       # Updated with MCP dependencies
├── .env                  # Environment variables
├── data/                 # Data directory
│   ├── test_health_data/ # Test health data files
│   ├── biomarkers.json   # Biomarker definitions
│   ├── protocols.json    # Health protocols
│   └── test_database.db  # SQLite database
├── src/
│   ├── bio_age_coach/    # Main package directory
│   │   ├── __init__.py
│   │   ├── chatbot/     # Chatbot logic
│   │   │   ├── __init__.py
│   │   │   ├── coach.py
│   │   │   └── prompts.py
│   │   └── mcp/        # MCP implementations
│   │       ├── __init__.py
│   │       ├── base.py
│   │       ├── health_server.py
│   │       ├── research_server.py
│   │       ├── tools_server.py
│   │       ├── client.py
│   │       └── router.py
│   └── evaluations/     # Evaluation framework
│       ├── __init__.py
│       └── chatbot_eval.py
└── tests/              # Test suite
    ├── __init__.py
    ├── test_chatbot/
    ├── test_mcp/
    └── test_evaluations/

### 8. MCP Server Implementation ✅

#### 8.1 Base MCP Server (`src/mcp/base.py`)
```python
from typing import Dict, Any
import asyncio
from mcp import MCPServer

class BaseMCPServer(MCPServer):
    def __init__(self, api_key: str):
        super().__init__()
        self.api_key = api_key
        
    async def authenticate(self, request: Dict[str, Any]) -> bool:
        return request.get("api_key") == self.api_key
        
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        if not await self.authenticate(request):
            return {"error": "Authentication failed"}
        return await self._process_request(request)
    
    async def _process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError
```

#### 8.2 Health Server (`src/mcp/health_server.py`)
```python
import pandas as pd
from typing import Dict, Any
from .base import BaseMCPServer

class HealthServer(BaseMCPServer):
    def __init__(self, api_key: str, health_data_path: str):
        super().__init__(api_key)
        self.health_data_path = health_data_path
        self.health_data = None
        
    async def _load_health_data(self):
        if self.health_data is None:
            self.health_data = pd.read_csv(self.health_data_path)
            
    async def _process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        await self._load_health_data()
        query_type = request.get("type")
        
        if query_type == "metrics":
            return await self._get_health_metrics()
        elif query_type == "trends":
            return await self._get_health_trends()
        
        return {"error": "Invalid query type"}
```

#### 8.3 Research Server (`src/mcp/research_server.py`)
```python
from typing import Dict, Any
from .base import BaseMCPServer

class ResearchServer(BaseMCPServer):
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.papers_cache = {}
        
    async def _process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        query = request.get("query", "")
        
        if query in self.papers_cache:
            return self.papers_cache[query]
            
        # Simple keyword-based search for MVP
        # TODO: Replace with vector database in future
        results = await self._search_papers(query)
        self.papers_cache[query] = results
        return results
```

#### 8.4 Tools Server (`src/mcp/tools_server.py`)
```python
from typing import Dict, Any
from .base import BaseMCPServer

class ToolsServer(BaseMCPServer):
    async def _process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        tool_name = request.get("tool")
        
        if tool_name == "biological_age":
            return await self._calculate_biological_age(request.get("data", {}))
        elif tool_name == "health_score":
            return await self._calculate_health_score(request.get("data", {}))
            
        return {"error": "Unknown tool"}
        
    async def _calculate_biological_age(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # Implement biological age calculation
        # This is a placeholder for the actual implementation
        return {"biological_age": 0.0}
```

#### 8.5 Query Router (`src/mcp/router.py`)
```python
from typing import Dict, Any
import re

class QueryRouter:
    def __init__(self):
        self.health_patterns = [
            r"health data",
            r"metrics",
            r"measurements",
            r"apple health"
        ]
        self.research_patterns = [
            r"research",
            r"study",
            r"paper",
            r"evidence"
        ]
        self.tools_patterns = [
            r"calculate",
            r"compute",
            r"estimate",
            r"biological age"
        ]
    
    def route_query(self, query: str) -> str:
        query = query.lower()
        
        if any(re.search(pattern, query) for pattern in self.health_patterns):
            return "health"
        elif any(re.search(pattern, query) for pattern in self.research_patterns):
            return "research"
        elif any(re.search(pattern, query) for pattern in self.tools_patterns):
            return "tools"
            
        return "unknown"
```

### 9. Streamlit Integration Update ✅

#### 9.1 MCP Client Setup (`app.py` updates)
```python
from mcp import MultiServerMCPClient
from src.mcp.health_server import HealthServer
from src.mcp.research_server import ResearchServer
from src.mcp.tools_server import ToolsServer
from src.mcp.router import QueryRouter

# Initialize MCP servers
async def init_mcp_servers():
    api_key = os.getenv("MCP_API_KEY")
    health_data_path = "data/test_health_data/export.csv"
    
    servers = {
        "health": HealthServer(api_key, health_data_path),
        "research": ResearchServer(api_key),
        "tools": ToolsServer(api_key)
    }
    
    client = MultiServerMCPClient()
    for name, server in servers.items():
        await client.add_server(name, server)
    
    return client

# Initialize session state for MCP
if "mcp_client" not in st.session_state:
    st.session_state.mcp_client = asyncio.run(init_mcp_servers())
    st.session_state.query_router = QueryRouter()
```

#### 9.2 Query Processing Update
```python
async def process_user_query(query: str) -> str:
    # Route query to appropriate server
    server_type = st.session_state.query_router.route_query(query)
    
    if server_type == "unknown":
        return "I'm not sure how to process this query. Could you be more specific?"
    
    try:
        response = await st.session_state.mcp_client.send_request(
            server_type,
            {
                "query": query,
                "api_key": os.getenv("MCP_API_KEY")
            }
        )
        return format_response(response)
    except Exception as e:
        return f"Error processing query: {str(e)}"
```

### 10. Security Implementation 🔄
- [ ] Set up API key management
- [ ] Implement request authentication
- [ ] Add input validation and sanitization

### 11. Testing Updates 🔄
- [x] Create basic MCP server test suite
- [x] Implement initial integration tests
- [ ] Add comprehensive test cases for routing
- [ ] Add performance benchmarks
- [ ] Create context-aware evaluation framework
- [ ] Implement MCP-specific test scenarios

### 12. Health Data Management 🆕
- [ ] Standardize test data format
- [ ] Create health data validation schema
- [ ] Implement data versioning
- [ ] Add data migration tools
- [ ] Create data cleanup utilities

### 13. Evaluation Framework Updates 🆕
- [ ] Create MCP-specific test cases
- [ ] Add routing context validation
- [ ] Implement prompt verification
- [ ] Add server response validation
- [ ] Create comprehensive test scenarios
- [ ] Add performance metrics for routing

### Next Steps

#### Immediate Actions (Current Sprint)
1. **Health Data Standardization (1 week)**
   - Define standard test data format
   - Create validation schema
   - Implement data cleanup tools
   - Add versioning support

2. **Evaluation Framework Enhancement (1 week)**
   - Create MCP-aware test cases
   - Add routing context validation
   - Implement prompt testing
   - Add server response validation

3. **Testing & Documentation (1 week)**
   - Update test suite
   - Add new test scenarios
   - Document data formats
   - Create testing guides

## Part 3: Future Enhancements 🔄

### 14. Database Integration for User Health Data
- [ ] Implement database connection and queries
- [ ] Create data mapper for health records
- [ ] Build initialization flow
- [ ] Add data completeness assessment
- [ ] Develop intelligent prompting

### 15. Prompt Engineering Evolution
- [ ] Analyze conversation logs
- [ ] Create specialized templates
- [ ] Implement A/B testing
- [ ] Design persona-based prompts
- [ ] Add context-aware prompting

### 16. Advanced Analytics
- [ ] Implement trend analysis
- [ ] Create personalized targets
- [ ] Build recommendation engine
- [ ] Design progress tracking
- [ ] Add adaptive coaching

## Dependencies Update (`requirements.txt`)
```
streamlit>=1.24.0
pandas>=2.0.0
numpy>=1.24.0
matplotlib>=3.7.0
python-dotenv>=1.0.0
mcp>=1.0.0  # Add actual version
aiohttp>=3.8.0
pytest>=7.0.0
pytest-asyncio>=0.21.0
```

## Next Steps

### Immediate Actions (Phase 1)
1. **MCP Server Setup (1 week)**
   - Create base MCP server class
   - Implement health data server
   - Add research paper server
   - Build tools server
   - Set up query router

2. **Integration (1 week)**
   - Update Streamlit app
   - Add MCP client setup
   - Implement query processing
   - Test end-to-end flow

3. **Testing & Security (1 week)**
   - Set up test suite
   - Add authentication
   - Implement validation
   - Run performance tests

### Mid-Term Goals (Phase 2)
1. Move MCP servers to separate processes
2. Add proper research database
3. Enhance query routing with LLM
4. Implement advanced metrics

### Long-Term Vision (Phase 3)
1. Deploy as microservices
2. Add vector database
3. Enable real-time sync
4. Build analytics dashboard 