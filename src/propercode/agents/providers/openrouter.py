from typing import Any
from keyring import get_password

from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openrouter import OpenRouterProvider as PydanticOpenRouterProvider

from propercode.agents.providers.base import BaseProvider

class OpenRouterProvider(BaseProvider):
    '''
    Open Router LLM Provider
    '''

    def __init__(self):
        self._api_key = get_password("propercode","openrouter_api")
        if not self._api_key:
            raise ValueError("API Key is not available")
        
        self.client = PydanticOpenRouterProvider(api_key=self._api_key)
    
    def get_chat_model(self, model_name: str) -> Any:
        return OpenAIChatModel(model_name=model_name,provider=self.client)