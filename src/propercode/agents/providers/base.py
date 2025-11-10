from abc import ABC,abstractmethod
from typing import Any

class BaseProvider(ABC):
    '''
    Base class for all LLM Providers
    '''
    @abstractmethod
    def get_chat_model(self,model_name:str)->Any:
        '''
        Returns the model instance from the provider
        '''
        pass