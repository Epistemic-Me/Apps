"""General Agent for handling general conversation and queries."""

from typing import Dict, Any, List, Optional
from bio_age_coach.agents.base_agent import Agent
from bio_age_coach.router.observation_context import ObservationContext

class GeneralAgent(Agent):
    """Agent for handling general conversation, greetings, and non-specialized queries."""
    
    def __init__(self, name: str, description: str, api_key: str, mcp_client):
        """Initialize the General agent.
        
        Args:
            name: Name of the agent
            description: Description of the agent's capabilities
            api_key: OpenAI API key
            mcp_client: MCP client for server communication
        """
        super().__init__(
            name=name,
            description=description,
            api_key=api_key,
            mcp_client=mcp_client
        )
    
    def _initialize_capabilities(self) -> None:
        """Initialize the capabilities of this agent."""
        self.capabilities = [
            "Handle general conversation",
            "Process greetings and farewells",
            "Provide app information",
            "Answer general questions",
            "Explain app features",
            "Handle small talk",
            "Provide general health advice",
            "Redirect to specialized agents when needed"
        ]
    
    def _initialize_servers(self) -> None:
        """Initialize server types this agent will communicate with."""
        self.server_types = {"general"}
        
    def _initialize_domain_examples(self) -> None:
        """Initialize examples of queries this agent can handle."""
        self.domain_examples = [
            "Hello",
            "How are you?",
            "What can you do?",
            "What is this app for?",
            "Tell me about yourself",
            "How does this app work?",
            "What features does this app have?",
            "Can you help me?",
            "I'm new here",
            "Goodbye",
            "Thanks for your help",
            "What should I do next?",
            "I'm confused",
            "Who created this app?",
            "How do I use this app?"
        ]
        
    def _initialize_supported_data_types(self) -> None:
        """Initialize data types this agent can process."""
        self.supported_data_types = {"general"}
    
    async def can_handle(self, query: str, context: Dict[str, Any]) -> float:
        """Determine if this agent can handle the query.
        
        Args:
            query: User query
            context: Conversation context
            
        Returns:
            float: Confidence score between 0 and 1
        """
        # Check for greeting keywords
        greeting_keywords = [
            "hello", "hi", "hey", "greetings", "good morning", "good afternoon", 
            "good evening", "howdy", "what's up", "how are you"
        ]
        
        # Check for app information keywords
        app_keywords = [
            "app", "application", "program", "software", "tool", "feature", 
            "what can you do", "how do you work", "what is this", "how does this work",
            "help me", "explain", "tell me about", "what should i do"
        ]
        
        # Check for farewell keywords
        farewell_keywords = [
            "goodbye", "bye", "see you", "farewell", "thanks", "thank you", 
            "appreciate", "that's all", "that is all"
        ]
        
        # Calculate confidence based on keyword matches
        query_lower = query.lower()
        
        # High confidence for greetings and farewells
        if any(keyword in query_lower for keyword in greeting_keywords):
            return 0.9
        
        if any(keyword in query_lower for keyword in farewell_keywords):
            return 0.9
        
        # Medium-high confidence for app information
        if any(keyword in query_lower for keyword in app_keywords):
            return 0.8
        
        # Medium confidence for very short queries (likely general conversation)
        if len(query.split()) < 4:
            return 0.7
        
        # Low-medium confidence as fallback
        return 0.4
    
    async def process(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process the query and return a response.
        
        Args:
            query: User query
            context: Conversation context
            
        Returns:
            Dict[str, Any]: Response
        """
        try:
            # Categorize the query
            query_lower = query.lower()
            
            # Handle greetings
            if any(keyword in query_lower for keyword in ["hello", "hi", "hey", "greetings", "good morning", "good afternoon", "good evening"]):
                return await self._process_greeting(query, context)
            
            # Handle farewells
            elif any(keyword in query_lower for keyword in ["goodbye", "bye", "see you", "farewell", "thanks", "thank you"]):
                return await self._process_farewell(query)
            
            # Handle app information requests
            elif any(keyword in query_lower for keyword in ["what can you do", "how do you work", "what is this", "how does this work", "feature", "app"]):
                return await self._process_app_info(query)
            
            # Handle help requests
            elif any(keyword in query_lower for keyword in ["help", "confused", "don't understand", "explain"]):
                return await self._process_help_request(query)
            
            # Handle general conversation
            else:
                return await self._process_general_conversation(query, context)
                
        except Exception as e:
            return {
                "response": "I'm sorry, I encountered an error processing your request. How else can I help you?",
                "suggestions": [
                    "Tell me about the app",
                    "How can I improve my biological age?",
                    "What health data can I track?"
                ],
                "error": str(e)
            }
    
    async def _process_greeting(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process greeting query.
        
        Args:
            query: User query
            context: Conversation context
            
        Returns:
            Dict[str, Any]: Response
        """
        # Check if this is a returning user
        user_name = context.get("user_name", "")
        is_returning = context.get("is_returning", False)
        
        if user_name and is_returning:
            greeting = f"Hello again, {user_name}! It's great to see you back."
            suggestions = [
                "Show me my latest bio age score",
                "What's changed since my last visit?",
                "How can I improve my health metrics?"
            ]
        elif user_name:
            greeting = f"Hello, {user_name}! How can I help you today?"
            suggestions = [
                "What can this app do?",
                "How is biological age calculated?",
                "How can I track my health data?"
            ]
        else:
            greeting = "Hello! I'm your Bio Age Coach, here to help you understand and optimize your biological age. How can I assist you today?"
            suggestions = [
                "What is biological age?",
                "What can this app do?",
                "How do I get started?"
            ]
        
        return {
            "response": greeting,
            "suggestions": suggestions,
            "error": None
        }
    
    async def _process_farewell(self, query: str) -> Dict[str, Any]:
        """Process farewell query.
        
        Args:
            query: User query
            
        Returns:
            Dict[str, Any]: Response
        """
        if "thank" in query.lower():
            return {
                "response": "You're welcome! I'm here whenever you need assistance with your health optimization journey. Have a great day!",
                "suggestions": [],
                "error": None
            }
        else:
            return {
                "response": "Goodbye! Remember that consistent small changes lead to significant improvements in your biological age over time. Looking forward to our next conversation!",
                "suggestions": [],
                "error": None
            }
    
    async def _process_app_info(self, query: str) -> Dict[str, Any]:
        """Process app information query.
        
        Args:
            query: User query
            
        Returns:
            Dict[str, Any]: Response
        """
        if "feature" in query.lower() or "can you do" in query.lower():
            return {
                "response": "The Bio Age Coach app offers several features to help you optimize your biological age:",
                "suggestions": [
                    "Track and analyze your biological age",
                    "Get personalized health recommendations",
                    "Monitor sleep, exercise, and other health metrics",
                    "Learn about the science of aging",
                    "Connect with health devices and apps"
                ],
                "error": None
            }
        elif "how" in query.lower() and "work" in query.lower():
            return {
                "response": "The Bio Age Coach works by analyzing your health data to calculate your biological age and provide personalized recommendations. Here's how it works:",
                "suggestions": [
                    "1. Connect your health devices or manually input data",
                    "2. The app analyzes your metrics using scientific algorithms",
                    "3. You receive a biological age score and health insights",
                    "4. Follow personalized recommendations to improve your score",
                    "5. Track your progress over time"
                ],
                "error": None
            }
        else:
            return {
                "response": "The Bio Age Coach is an AI-powered health optimization app designed to help you understand and improve your biological age. Unlike chronological age, biological age reflects how well your body is functioning and can be improved through lifestyle changes.",
                "suggestions": [
                    "What is biological age?",
                    "How is biological age calculated?",
                    "What features does the app have?",
                    "How do I get started?"
                ],
                "error": None
            }
    
    async def _process_help_request(self, query: str) -> Dict[str, Any]:
        """Process help request query.
        
        Args:
            query: User query
            
        Returns:
            Dict[str, Any]: Response
        """
        return {
            "response": "I'm here to help! The Bio Age Coach app can assist you with understanding and optimizing your biological age. Here are some things you can ask me about:",
            "suggestions": [
                "Explain biological age and how it's calculated",
                "Analyze my health data and provide insights",
                "Give recommendations to improve my biological age",
                "Provide scientific information about health and longevity",
                "Help me track my progress over time"
            ],
            "error": None
        }
    
    async def _process_general_conversation(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process general conversation query.
        
        Args:
            query: User query
            context: Conversation context
            
        Returns:
            Dict[str, Any]: Response
        """
        # Try to fetch a response from the general server
        try:
            response = await self.mcp_client.send_request(
                "general",
                {
                    "type": "conversation",
                    "query": query,
                    "context": context
                }
            )
            
            if "error" not in response and "response" in response:
                return {
                    "response": response["response"],
                    "suggestions": response.get("suggestions", []),
                    "error": None
                }
        except Exception:
            # Fall back to hardcoded response if server fails
            pass
        
        # Fallback response for general conversation
        return {
            "response": "I'm here to help you understand and optimize your biological age. Would you like to learn more about biological age, track your health metrics, or get personalized recommendations?",
            "suggestions": [
                "Tell me about biological age",
                "How can I improve my health metrics?",
                "What data can I track in this app?",
                "Give me some health recommendations"
            ],
            "error": None
        }
    
    async def create_observation_context(self, data_type: str, user_id: Optional[str] = None) -> Optional[ObservationContext]:
        """Create an observation context for the given data type.
        
        Args:
            data_type: Type of data to create context for
            user_id: Optional user ID
            
        Returns:
            Optional[ObservationContext]: Observation context or None if not supported
        """
        # General agent creates a generic observation context for general conversation
        if data_type == "general":
            return ObservationContext(agent_name=self.name, data_type=data_type, user_id=user_id)
        
        # General agent doesn't process specific data types
        return None 