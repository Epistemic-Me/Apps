from unittest.mock import MagicMock, create_autospec
from typing import Dict, Any, List, Optional
from deepeval.test_case import LLMTestCase as BaseLLMTestCase
from deepeval.test_case import ConversationalTestCase as BaseConversationalTestCase

class SessionStateMock:
    """Mock for Streamlit's session state that supports both dict and attribute access"""
    def __init__(self, initial_state: Dict[str, Any] = None):
        self._state = {}
        if initial_state:
            self._state.update(initial_state)
    
    def __getattr__(self, name: str) -> Any:
        if name not in self._state:
            self._state[name] = None
        return self._state[name]
    
    def __setattr__(self, name: str, value: Any) -> None:
        if name == '_state':
            super().__setattr__(name, value)
        else:
            self._state[name] = value
    
    def __getitem__(self, key: str) -> Any:
        if key not in self._state:
            self._state[key] = None
        return self._state[key]
    
    def __setitem__(self, key: str, value: Any) -> None:
        self._state[key] = value
    
    def __contains__(self, key: str) -> bool:
        return key in self._state
    
    def get(self, key: str, default: Any = None) -> Any:
        return self._state.get(key, default)

def create_llm_test_case(input_text: str, output_text: str, context: list = None) -> BaseLLMTestCase:
    """Create a LLMTestCase with the given input and output"""
    test_case = BaseLLMTestCase(
        input=input_text,
        actual_output=output_text,
        expected_output=None,
        context=context or [],
        retrieval_context=None,
        additional_metadata=None,
        comments=None,
        tools_called=None,
        expected_tools=None,
        name=None
    )
    return test_case

def create_conversational_test_case(turns: list = None, chatbot_role: str = None, name: str = None) -> BaseConversationalTestCase:
    """Create a ConversationalTestCase with the given turns"""
    test_case = BaseConversationalTestCase(
        turns=turns or [],
        chatbot_role=chatbot_role,
        name=name,
        additional_metadata=None,
        comments=None
    )
    return test_case 