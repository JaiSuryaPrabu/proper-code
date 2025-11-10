from typing import Optional,Dict,Any
from pydantic import BaseModel,Field

class SearchMemoryToolInput(BaseModel):
    '''
    Input schema for the search memory tool
    '''
    query:str = Field(...,description="The text query to search for in the memory content")
    limit:int = Field(default=3,description="The max number of memories to return")
    memory_type:Optional[str] = Field(default="sumary",description="Filter by memory like 'summary' or 'fact'")

class WriteMemoryToolInput(BaseModel):
    '''
    Input schema for the write tool
    '''
    session_id: str = Field(...,description="The unique ID of the current session")
    content: str = Field(...,description="The information or content to be store")
    memory_type:str = Field(default="summary",description="The type of memory being stored, e.g., 'summary' or 'fact'")
    metadata: Optional[Dict[str,Any]] = Field(default=None,description="Optional JSON metadata")