from pydantic import BaseModel,Field
from uuid import UUID,uuid4
from typing import List, Any

from propercode.models.agents.node_outputs import ContextNodeOutput,PlanNodeOutput,CodeNodeOutput,EvaluationNodeOutput

class AgentState(BaseModel):
    session_id:UUID = Field(default_factory=uuid4)
    user_prompt:str = Field(...,description="The user request",min_length=1)
    conversation_history:List[str] = Field(default_factory=list,description="Series of conversations")
    errors : List[str] = Field(default_factory=list,description="Series of errors")
    retries: int = Field(default=0,ge=0)
    max_retries: int = Field(default=0,ge=1)
    chat_model : Any = Field(None,description="The LLM Client instance")
    config: dict = Field(default_factory=dict,description="The runtime flags")

    context_output:ContextNodeOutput|None = Field(None,description="output of the context node")
    plan_output:PlanNodeOutput|None = Field(None,description="Plan node output")
    code_output:CodeNodeOutput|None = Field(None,description="Code node output")
    evaluation_output:EvaluationNodeOutput|None = Field(None,description="Evaluation node output")

    def append_history(self,msg:str) -> 'AgentState':
        history = self.conversation_history + [msg]
        return self.model_copy(update={'conversation_history':history})
    
    def add_error(self,err:str) -> 'AgentState':
        errors = self.errors + [err]
        return self.model_copy(update={'errors':errors})
    
    def increment_retries(self) -> 'AgentState':
        retries = self.retries + 1
        if retries > self.max_retries:
            raise ValueError('Maximum retries attained')
        return self.model_copy(update={'retries':retries})