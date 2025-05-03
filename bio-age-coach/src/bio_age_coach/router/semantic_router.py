"""
Semantic router for the Bio Age Coach multi-agent system.

Routes user queries to the appropriate agent based on semantic similarity
and contextual understanding.
"""

from typing import Dict, Any, List, Optional, Tuple, Union
import logging
import asyncio
import os
from openai import AsyncOpenAI
import numpy as np
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.schema import Document
from .observation_context import ObservationContext

class SemanticRouter:
    """Routes queries to appropriate agents based on semantic understanding.
    
    This router:
    - Uses embeddings to match queries to agent domains
    - Maintains conversation context for better routing decisions
    - Can dynamically adjust routing based on feedback
    - Handles data uploads and creates observation contexts
    """
    
    def __init__(self, api_key: str, agents: List[Any], llm_model: str = "gpt-4o-mini"):
        """Initialize the semantic router.
        
        Args:
            api_key: API key for LLM access
            agents: List of Agent instances to route queries to
            llm_model: LLM model to use for advanced routing
        """
        self.api_key = api_key
        self.agents = agents
        self.llm_model = llm_model
        self.client = AsyncOpenAI(api_key=api_key)
        self.embeddings = OpenAIEmbeddings(api_key=api_key)
        self.route_history: List[Dict[str, Any]] = []
        self.context: Dict[str, Dict[str, Any]] = {}  # User context storage
        self.observation_contexts: Dict[str, Dict[str, ObservationContext]] = {}  # User observation contexts
        
        # Vector store for semantic matching
        self.vector_store = None
        
        # Relevancy threshold for agent responses
        self.relevancy_threshold = 0.5
        
        # Initialize router components
        self._initialize()
    
    def _initialize(self) -> None:
        """Initialize router components."""
        # Prepare documents from agent domain examples
        documents = []
        for agent in self.agents:
            # Get domain examples from agent capabilities
            examples = getattr(agent, 'domain_examples', [])
            if not examples and hasattr(agent, 'capabilities'):
                # Use capabilities as examples if no domain examples
                examples = agent.capabilities
                
            for example in examples:
                documents.append(Document(
                    page_content=example,
                    metadata={"agent_name": agent.name}
                ))
        
        # Create vector store for semantic matching
        if documents:
            self.vector_store = FAISS.from_documents(documents, self.embeddings)
    
    async def route_query(self, user_id: str, query: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Route a query to the appropriate agent.
        
        Args:
            user_id: User ID
            query: User query
            metadata: Additional metadata
            
        Returns:
            Response from the agent
        """
        # Update context with the new query
        self._update_context(user_id, query, metadata)
        
        # Get context for this user
        user_context = self.context.get(user_id, {})
        
        # Check if this is a data upload
        if metadata and "data_upload" in metadata and metadata["data_upload"]:
            return await self._handle_data_upload(user_id, query, metadata, user_context)
        
        # Check if we have observation contexts for this user
        if user_id in self.observation_contexts and self.observation_contexts[user_id]:
            # Use observation contexts to determine relevancy
            return await self._route_with_observation_contexts(user_id, query, user_context)
        
        # Route to the most appropriate agent using semantic routing
        agent, confidence = await self._route(query, user_context)
        
        try:
            # Process the query with the selected agent
            response = await agent.process(query, user_context)
            
            # Ensure response has required fields
            if "response" not in response:
                response["response"] = "I processed your request but encountered an issue with the response format."
            
            if "insights" not in response:
                response["insights"] = []
                
            if "visualization" not in response:
                response["visualization"] = None
                
            if "error" not in response:
                response["error"] = None
                
            # Record routing decision
            self.route_history.append({
                "user_id": user_id,
                "query": query,
                "selected_agent": agent.name,
                "confidence": confidence,
                "timestamp": asyncio.get_event_loop().time()
            })
            
            return response
            
        except Exception as e:
            logging.error(f"Error processing query with agent {agent.name}: {e}")
            return {
                "response": "I encountered an error while processing your request.",
                "insights": [],
                "visualization": None,
                "error": str(e)
            }
    
    async def _handle_data_upload(self, user_id: str, query: str, metadata: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a data upload.
        
        Args:
            user_id: User ID
            query: User query accompanying the data upload
            metadata: Metadata about the upload
            user_context: User conversation context
            
        Returns:
            Response with insights from all relevant agents
        """
        data = metadata.get("data", {})
        data_type = metadata.get("data_type", "unknown")
        
        # Initialize observation contexts for this user if not already present
        if user_id not in self.observation_contexts:
            self.observation_contexts[user_id] = {}
        
        # Create or update observation contexts for each agent
        for agent in self.agents:
            if hasattr(agent, 'create_observation_context') and callable(agent.create_observation_context):
                try:
                    # Create observation context for this agent
                    observation_context = await agent.create_observation_context(data_type, user_id)
                    
                    if observation_context:
                        # Update with the new data
                        observation_context.update_from_data(data)
                        
                        # Calculate relevancy score
                        relevancy = observation_context.calculate_relevancy(query)
                        
                        # Store the observation context
                        self.observation_contexts[user_id][agent.name] = observation_context
                except Exception as e:
                    logging.error(f"Error creating observation context for agent {agent.name}: {e}")
        
        # Get responses from all agents with relevant observation contexts
        return await self._route_with_observation_contexts(user_id, query, user_context)
    
    async def _route_with_observation_contexts(self, user_id: str, query: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Route a query using observation contexts.
        
        Args:
            user_id: User ID
            query: User query
            user_context: User conversation context
            
        Returns:
            Response with insights from all relevant agents
        """
        print(f"Routing with observation contexts for user {user_id}")
        print(f"Query: {query}")
        print(f"Available observation contexts: {list(self.observation_contexts.get(user_id, {}).keys())}")
        
        # Calculate relevancy scores for each agent's observation context
        agent_scores = []
        for agent_name, observation_context in self.observation_contexts[user_id].items():
            # Calculate relevancy score
            relevancy = observation_context.calculate_relevancy(query)
            print(f"Agent {agent_name} relevancy: {relevancy}")
            
            # Add to list if above threshold
            if relevancy >= self.relevancy_threshold:
                agent_scores.append((agent_name, relevancy, observation_context))
        
        # Sort by relevancy score (highest first)
        agent_scores.sort(key=lambda x: x[1], reverse=True)
        print(f"Sorted agent scores: {[(name, score) for name, score, _ in agent_scores]}")
        
        if not agent_scores:
            print("No relevant observation contexts, falling back to semantic routing")
            # No relevant observation contexts, fall back to semantic routing
            agent, confidence = await self._route(query, user_context)
            print(f"Selected agent via semantic routing: {agent.name}, confidence: {confidence}")
            
            try:
                # Process the query with the selected agent
                response = await agent.process(query, user_context)
                
                # Ensure response has required fields
                response = self._ensure_response_format(response)
                
                # Record routing decision
                self.route_history.append({
                    "user_id": user_id,
                    "query": query,
                    "selected_agent": agent.name,
                    "confidence": confidence,
                    "timestamp": asyncio.get_event_loop().time(),
                    "method": "semantic"
                })
                
                print(f"Returning response from agent {agent.name}")
                print(f"Response type: {type(response)}")
                print(f"Response keys: {list(response.keys()) if isinstance(response, dict) else 'Not a dict'}")
                
                return response
                
            except Exception as e:
                logging.error(f"Error processing query with agent {agent.name}: {e}")
                print(f"Error processing query with agent {agent.name}: {e}")
                return self._ensure_response_format({
                    "response": "I encountered an error while processing your request.",
                    "error": str(e)
                })
        
        # Generate responses from all relevant agents
        agent_responses = []
        for agent_name, relevancy, observation_context in agent_scores:
            # Generate response from observation context
            print(f"Generating response from observation context for agent {agent_name}")
            response = observation_context.generate_response()
            
            # Ensure response has required fields
            response = self._ensure_response_format(response)
            
            # Add agent name and relevancy score
            response["agent_name"] = agent_name
            response["relevancy_score"] = relevancy
            
            agent_responses.append(response)
            
            # Record routing decision
            self.route_history.append({
                "user_id": user_id,
                "query": query,
                "selected_agent": agent_name,
                "confidence": relevancy,
                "timestamp": asyncio.get_event_loop().time(),
                "method": "observation_context"
            })
        
        # Combine responses
        print(f"Combining responses from {len(agent_responses)} agents")
        combined_response = self._combine_responses(agent_responses)
        
        # Log the combined response
        print(f"Combined response type: {type(combined_response)}")
        print(f"Combined response keys: {list(combined_response.keys()) if isinstance(combined_response, dict) else 'Not a dict'}")
        
        # Ensure the combined response has a valid format
        return self._ensure_response_format(combined_response)
    
    def _combine_responses(self, responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Combine responses from multiple agents.
        
        Args:
            responses: List of responses from different agents
            
        Returns:
            Combined response
        """
        if not responses:
            return self._ensure_response_format({
                "response": "I couldn't find any relevant information for your query.",
                "agent_responses": []
            })
        
        # Use the highest relevancy response as the main response
        main_response = responses[0]
        
        # Combine insights from all responses
        all_insights = []
        for response in responses:
            if "insights" in response and response["insights"]:
                for insight in response["insights"]:
                    if insight not in all_insights:
                        all_insights.append(insight)
        
        # Use the visualization from the highest relevancy response
        visualization = main_response.get("visualization")
        
        # Create a combined response
        combined = {
            "response": main_response.get("response", "I processed your query but couldn't generate a specific response."),
            "insights": all_insights,
            "visualization": visualization,
            "error": None,
            "agent_responses": responses  # Include all individual responses
        }
        
        return self._ensure_response_format(combined)
    
    def _ensure_response_format(self, response: Union[Dict[str, Any], str, None]) -> Dict[str, Any]:
        """Ensure the response has the required fields and proper format.
        
        Args:
            response: Response to check and update
            
        Returns:
            A properly formatted response dictionary
        """
        # If response is None, create a default response
        if response is None:
            return {
                "response": "I processed your request but couldn't generate a specific response.",
                "insights": [],
                "visualization": None,
                "error": None
            }
            
        # If response is a string, convert it to a dict
        if isinstance(response, str):
            return {
                "response": response,
                "insights": [],
                "visualization": None,
                "error": None
            }
            
        # If response is already a dict, ensure it has all required fields
        if isinstance(response, dict):
            # Make a copy to avoid modifying the original
            formatted_response = response.copy()
            
            # Ensure response field exists and is not None
            if "response" not in formatted_response or formatted_response["response"] is None:
                formatted_response["response"] = "I processed your request but couldn't generate a specific response."
            
            # Ensure insights field exists
            if "insights" not in formatted_response:
                formatted_response["insights"] = []
            elif formatted_response["insights"] is None:
                formatted_response["insights"] = []
                
            # Ensure visualization field exists
            if "visualization" not in formatted_response:
                formatted_response["visualization"] = None
                
            # Ensure error field exists
            if "error" not in formatted_response:
                formatted_response["error"] = None
                
            return formatted_response
        
        # If response is some other type, convert to string and create a dict
        return {
            "response": str(response),
            "insights": [],
            "visualization": None,
            "error": None
        }
    
    async def _route(self, query: str, context: Dict[str, Any]) -> Tuple[Any, float]:
        """Route a query to the most appropriate agent.
        
        Args:
            query: The user's query
            context: Conversation context
            
        Returns:
            Tuple of (selected agent, confidence score)
        """
        # First try semantic routing with embeddings
        agent, confidence = await self._semantic_route(query)
        
        # If confidence is low, use agent-based routing
        if confidence < 0.7:
            # Ask each agent for its confidence in handling the query
            agent_confidences = []
            for agent in self.agents:
                if hasattr(agent, 'can_handle') and callable(agent.can_handle):
                    try:
                        agent_confidence = await agent.can_handle(query, context)
                        agent_confidences.append((agent, agent_confidence))
                    except Exception as e:
                        logging.error(f"Error getting confidence from agent {agent.name}: {e}")
                        agent_confidences.append((agent, 0.0))
            
            # Sort by confidence (highest first)
            agent_confidences.sort(key=lambda x: x[1], reverse=True)
            
            # If any agent has higher confidence than semantic routing
            if agent_confidences and agent_confidences[0][1] > confidence:
                agent, confidence = agent_confidences[0]
        
        return agent, confidence
    
    async def _semantic_route(self, query: str) -> Tuple[Any, float]:
        """Route based on semantic similarity.
        
        Args:
            query: The user's query
            
        Returns:
            Tuple of (selected agent, confidence score)
        """
        if self.vector_store is None:
            # Fallback to first agent if vector store not initialized
            return self.agents[0], 0.5
        
        try:
            # Get most similar documents
            results = self.vector_store.similarity_search_with_score(query, k=3)
            
            if not results:
                return self.agents[0], 0.5
            
            # Count agent matches in top results
            agent_scores: Dict[str, List[float]] = {}
            for doc, score in results:
                agent_name = doc.metadata.get("agent_name")
                if agent_name:
                    if agent_name not in agent_scores:
                        agent_scores[agent_name] = []
                    # Convert distance to similarity (0-1)
                    similarity = 1.0 - min(1.0, score)
                    agent_scores[agent_name].append(similarity)
            
            # Calculate average score for each agent
            avg_scores = {}
            for agent_name, scores in agent_scores.items():
                avg_scores[agent_name] = sum(scores) / len(scores)
            
            if not avg_scores:
                return self.agents[0], 0.5
            
            # Select agent with highest score
            best_agent_name = max(avg_scores, key=avg_scores.get)
            best_score = avg_scores[best_agent_name]
            
            # Find the actual agent object
            for agent in self.agents:
                if agent.name == best_agent_name:
                    return agent, best_score
            
            # Fallback
            return self.agents[0], 0.5
            
        except Exception as e:
            logging.error(f"Error in semantic routing: {e}")
            return self.agents[0], 0.5
    
    def _update_context(self, user_id: str, query: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Update conversation context with new query."""
        if user_id not in self.context:
            self.context[user_id] = {
                "queries": [],
                "metadata": {}
            }
            
        # Add the new query to the context
        self.context[user_id]["queries"].append({
            "text": query,
            "metadata": metadata or {}
        })
        
        # Limit the number of queries stored in context
        max_queries = 10
        if len(self.context[user_id]["queries"]) > max_queries:
            self.context[user_id]["queries"] = self.context[user_id]["queries"][-max_queries:]
            
        # Update metadata if provided
        if metadata:
            self.context[user_id]["metadata"].update(metadata)
    
    def update_context(self, user_id: str, context_update: Dict[str, Any]) -> None:
        """Update the context for a user with arbitrary context data.
        
        Args:
            user_id: The user ID
            context_update: Dictionary containing context data to update
        """
        if user_id not in self.context:
            self.context[user_id] = {
                "queries": [],
                "metadata": {}
            }
            
        # Update metadata with the provided context update
        if "metadata" not in self.context[user_id]:
            self.context[user_id]["metadata"] = {}
            
        self.context[user_id]["metadata"].update(context_update)
    
    def get_active_topic(self, user_id: str) -> Optional[str]:
        """Get currently active topic for a user."""
        return self.context.get(user_id, {}).get("active_topic")
    
    def clear_context(self, user_id: str) -> None:
        """Clear conversation context for a user."""
        if user_id in self.context:
            del self.context[user_id]
            
        if user_id in self.observation_contexts:
            del self.observation_contexts[user_id] 