from uuid import uuid4
from typing import Tuple
from pydantic_graph import Graph

from propercode.agents.nodes.plan import PlanNode
from propercode.agents.nodes.context import ContextNode
from propercode.agents.nodes.code_eval import CodeNode,EvaluationNode
from propercode.agents.memory.state import AgentState
from propercode.agents.memory.store import MemoryStore
from propercode.agents.memory.manager import MemoryManager
from propercode.agents.providers.openrouter import OpenRouterProvider

class CodeOrchestrator:
    '''
    Main agent
    '''
    def __init__(self,model_name:str,prune_days:int=30,prune_prob:float=0.1):
        self.model_name=model_name
        self.graph = Graph[AgentState,None,str](nodes=[ContextNode,PlanNode,CodeNode,EvaluationNode])
        self.memory_store = MemoryStore()
        self.memory_manager = MemoryManager(store=self.memory_store,prune_prob=prune_prob)
        self.memory_manager.prune(prune_days)
        self._chat_model = None

    def _get_chat_model(self):
        if self._chat_model is None:
            provider = OpenRouterProvider()
            self._chat_model = provider.get_chat_model(self.model_name)
        return self._chat_model

    async def run(self,state:AgentState) -> Tuple[str,AgentState]:
        '''
        Runs the agent
        '''
        state = state.model_copy(update={
            "session_id": uuid4()
        })

        state = state.model_copy(update={"chat_model":self._get_chat_model()})

        await self.memory_manager.prime(state)

        try:
            run_result = await self.graph.run(ContextNode(),state=state)
            final_output = run_result.output or "Completed"
            final_state = state

            if not final_state.errors:
                await self.memory_manager.summarize_and_save(final_state)
            return final_output,final_state
        except Exception as e:
            raise e
        finally:
            self.memory_store.close_conn()