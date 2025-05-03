# Conversation Modules Documentation

## Overview
Conversation modules are the core components of the Bio Age Coach system, each responsible for handling specific health topics and coordinating responses across multiple servers. This document outlines the architecture, implementation, and best practices for conversation modules.

## Architecture

### Module Components
1. **Router**: Routes user queries to appropriate conversation modules based on context
2. **Conversation Module**: Manages conversation state and coordinates server interactions
3. **Servers**: Specialized servers (e.g., BioAgeScoreServer, HealthServer) that handle specific functionality

### Key Concepts
- Each route maps to exactly one conversation module
- Modules can interact with multiple servers to provide comprehensive responses
- Servers are specialized by functionality (e.g., bio-age scoring, health data processing)
- Modules maintain conversation state and context

## Implementation

### Module Structure
```python
class ConvoModule:
    def __init__(self):
        self.resources = {}  # Resources by server type
        self.tools = {}      # Tools by server type
        self.prompts = {}    # Prompts that work across servers
        self.state = {}      # Conversation state
        
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process requests using appropriate servers."""
        pass
```

### Server Integration
```python
class BioAgeScoreModule(ConvoModule):
    def __init__(self):
        super().__init__()
        self.bio_age_server = BioAgeScoreServer()
        self.health_server = HealthServer()
        
    async def initialize(self):
        """Initialize servers and resources."""
        await self.bio_age_server.initialize()
        await self.health_server.initialize()
```

## Testing and Evaluation

### Module Testing Philosophy
The evaluation framework tests conversation modules as complete units, including:
- Prompt effectiveness and response quality
- Resource and tool coordination across servers
- State management and context handling
- End-to-end conversation flows

### Evaluation Framework
```python
class EvaluationSuite:
    def __init__(self, context: RouterContext):
        self.context = context
        self.module = None  # Will hold the module being tested
        self.metrics = [
            "response_quality",
            "tool_usage",
            "context_awareness",
            "prompt_effectiveness"
        ]
    
    async def setup(self):
        """Initialize module and test data."""
        # Generate test data
        test_data = self._generate_test_data()
        
        # Initialize module
        self.module = YourModule(api_key, self.context.mcp_client)
        await self.module.initialize(test_data)
```

### Test Data Generation
Test data should include:
1. **Time Series Data**: Health metrics over time
2. **Pattern Variations**: 
   - Consistent patterns
   - Improving trends
   - Declining trends
   - Weekend variations
3. **User Context**:
   - Habits and preferences
   - Goals and plans
   - Historical data

Example:
```python
def _generate_test_data(self):
    patterns = [
        {"name": "consistent", "metrics": {...}},
        {"name": "improving", "metrics": {...}},
        {"name": "weekend_dip", "metrics": {...}}
    ]
    return generate_data_with_patterns(patterns)
```

### Test Cases
Each test case verifies:
1. **Module Response Quality**
   - Accuracy of information
   - Proper use of prompts
   - Context-appropriate responses

2. **Tool Usage Patterns**
   - Correct tool selection
   - Proper parameter passing
   - Response handling

3. **Multi-Server Coordination**
   - Data aggregation
   - Cross-server analysis
   - Consistent state management

Example test case:
```python
test_case = ConversationalTestCase(
    input="What's my current health status?",
    expected_output="Health status analysis...",
    context=["User data", "Clinical guidelines"],
    tools_called=[
        ToolCall(
            name="health_module",
            args={"action": "analyze_status"},
            response={
                "metrics": {...},
                "analysis": {...},
                "recommendations": [...]
            }
        )
    ]
)
```

### Running Evaluations
```python
async def run_evaluation():
    # Initialize MCP client
    mcp_client = MultiServerMCPClient()
    
    # Create evaluation context
    context = RouterContext(mcp_client=mcp_client)
    
    # Run evaluation suite
    evaluation = YourModuleEvaluation(context)
    await evaluation.setup()
    results = await evaluation.run_evaluation()
```

### Evaluation Metrics
1. **Response Quality (40%)**
   - Accuracy: Correct information and calculations
   - Completeness: All relevant information included
   - Clarity: Well-structured and understandable
   - Context: Appropriate to user situation

2. **Tool Usage (30%)**
   - Selection: Right tools for the task
   - Parameters: Correct parameter values
   - Sequence: Logical tool call order
   - Error Handling: Proper error management

3. **Context Awareness (20%)**
   - User History: Considers past interactions
   - Preferences: Respects user preferences
   - Adaptation: Adjusts to changing context
   - Consistency: Maintains context across calls

4. **Prompt Effectiveness (10%)**
   - Engagement: Natural conversation flow
   - Guidance: Clear next steps
   - Personalization: Tailored to user
   - Format: Proper response formatting

### Best Practices

#### Test Design
1. **Comprehensive Coverage**
   - Test all module capabilities
   - Include edge cases
   - Test error conditions
   - Verify prompt variations

2. **Realistic Scenarios**
   - Use real-world patterns
   - Include typical variations
   - Test common user flows
   - Simulate actual usage

3. **Data Quality**
   - Generate realistic test data
   - Include various patterns
   - Maintain data consistency
   - Document data assumptions

4. **Evaluation Process**
   - Regular test runs
   - Metric tracking
   - Performance analysis
   - Continuous improvement

### Example: BioAge Score Module Evaluation

```python
class BioAgeScoreEvaluation(EvaluationSuite):
    async def setup(self):
        """Setup test environment."""
        # Generate test data with patterns
        test_data = self._generate_test_data()
        
        # Initialize module
        self.module = BioAgeScoreModule(
            api_key, 
            self.context.mcp_client
        )
        await self.module.initialize(test_data)
    
    def create_test_cases(self):
        """Create test cases."""
        return [
            self._create_score_calculation_test(),
            self._create_trend_analysis_test(),
            self._create_recommendations_test()
        ]
```

### Troubleshooting

#### Common Issues
1. **Test Failures**
   - Check test data quality
   - Verify module initialization
   - Review tool configurations
   - Check prompt templates

2. **Performance Issues**
   - Monitor response times
   - Check resource usage
   - Optimize tool calls
   - Cache where appropriate

3. **Integration Problems**
   - Verify server connections
   - Check client configuration
   - Review error handling
   - Test state management

### Maintenance

#### Regular Tasks
1. **Test Updates**
   - Add new test cases
   - Update existing tests
   - Maintain test data
   - Review metrics

2. **Performance Monitoring**
   - Track response times
   - Monitor success rates
   - Analyze failures
   - Optimize bottlenecks

3. **Documentation**
   - Update test descriptions
   - Document new patterns
   - Maintain examples
   - Track changes

## Best Practices

### Module Design
1. Single Responsibility: Each module handles one health topic
2. Clear Boundaries: Well-defined interfaces between modules
3. State Management: Maintain minimal necessary state
4. Error Handling: Graceful degradation on server failures

### Server Coordination
1. Clear Communication: Well-defined server interfaces
2. Efficient Routing: Smart request distribution
3. Error Recovery: Handle server unavailability
4. Data Consistency: Maintain consistent state across servers

### Testing
1. Comprehensive Coverage: Test all module functionality
2. Realistic Scenarios: Use real-world test cases
3. Edge Cases: Test error conditions and edge cases
4. Integration Testing: Verify multi-server coordination

## Example Implementation

### Bio Age Score Module
```python
class BioAgeScoreModule(ConvoModule):
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        # Process bio-age score related requests
        if request["type"] == "score_calculation":
            # Get health data from health server
            health_data = await self.health_server.get_health_data()
            
            # Calculate score using bio age server
            score = await self.bio_age_server.calculate_score(health_data)
            
            # Generate response using both servers' data
            return self._generate_response(score, health_data)
```

### Evaluation Example
```python
class BioAgeScoreEvaluation(EvaluationSuite):
    async def setup(self):
        """Setup test environment."""
        self.test_data = self._generate_test_data()
        await self.context.initialize_servers(self.test_data)
    
    def create_test_cases(self):
        """Create comprehensive test cases."""
        return [
            self._create_score_calculation_test(),
            self._create_trend_analysis_test(),
            self._create_improvement_recommendations_test()
        ]
```

## Troubleshooting

### Common Issues
1. Server Communication: Connection timeouts, API errors
2. State Management: Inconsistent state across servers
3. Context Handling: Missing or invalid context
4. Tool Usage: Incorrect tool sequences

### Solutions
1. Implement retry logic for server communication
2. Use transactions for multi-server operations
3. Validate context before processing
4. Log and monitor tool usage patterns

## Deployment

### Prerequisites
1. Server configurations
2. API keys and credentials
3. Test data and evaluation results
4. Monitoring setup

### Steps
1. Deploy servers independently
2. Configure module routing
3. Run evaluation suite
4. Monitor performance

## Maintenance

### Regular Tasks
1. Update test cases
2. Review evaluation results
3. Monitor server health
4. Update documentation

### Version Control
1. Track module changes
2. Document API updates
3. Maintain test coverage
4. Version documentation 