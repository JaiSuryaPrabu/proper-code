from pydantic import BaseModel,Field
from typing import Optional

class CLISettings(BaseModel):
    '''
    Defines the structures
    '''
    default_provider: Optional[str] = Field(default="openrouter",description="Default LLM provider like OpenAI etc")
    default_model: Optional[str] = Field(default="minimax/minimax-m2:free",description="the default LLM model to use")
    verbose: bool = Field(default=False,description="Enable verbose logging for debugging purpose")
