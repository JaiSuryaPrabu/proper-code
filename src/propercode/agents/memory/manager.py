import json

from propercode.agents.memory.store import MemoryStore
from propercode.agents.memory.state import AgentState
from propercode.agents.tools.memory import SearchMemoryTool,WriteMemoryTool
from propercode.models.agents.memory_models import SearchMemoryToolInput,WriteMemoryToolInput

class MemoryManager:
    '''
    Manages the memory for the multi-agent
    '''
    def __init__(self,store:MemoryStore,prune_prob:float=0.1):
        self.store = store
        self.prune_prob = prune_prob
        self.search_memory_tool = SearchMemoryTool(self.store)
        self.write_memory_tool = WriteMemoryTool(self.store)
    
    async def prime(self,state:AgentState) -> AgentState:
        '''
        Searches the memories
        '''
        try:
            search_input = SearchMemoryToolInput(query=state.user_prompt,limit=2,memory_type="summary")
            results = await self.search_memory_tool.run(search_input)

            if results:
                priming_msg = f"Pre-computed memories:\n{results}"
                return state.append_history(priming_msg)
            return state
        except Exception as e:
            return state.add_error(f"Prime failed: {e}")
    
    async def summarize_and_save(self,state:AgentState) -> AgentState:
        '''
        Saves history and summary
        '''
        try:
            history_json = json.dumps(state.conversation_history, indent=2, ensure_ascii=False)
            self.store.save_conversation(
                str(state.session_id), state.user_prompt, history_json
            )

            verdict = (state.evaluation.verdict.value if state.evaluation else "UNKNOWN")
            summary_text = f"Summary: user asked for {state.user_prompt}, code was generated and {verdict.lower()} evaluation."

            write_memory_input = WriteMemoryToolInput(session_id=str(state.session_id),content=summary_text,memory_type="summary")

            await self.write_memory_tool.run(write_memory_input)

            return state
        except Exception as e:
            return state.add_error(f"Save failed: {e}")
    
    def prune(self, days_to_keep: int = 30) -> None:
        '''
        Prunes old memories
        '''
        try:
            self.store.prune_old_memories(days_to_keep=days_to_keep)
        except Exception as e:
            print(f"Prune failed: {e}")