from rich import print
from typing import Any
from pydantic_ai import Agent,ModelSettings
from pydantic_graph import BaseNode, GraphRunContext
from dataclasses import dataclass,field

from propercode.agents.nodes import CONTEXT_SYSTEM_PROMPT
from propercode.agents.memory.state import AgentState
from propercode.agents.nodes.plan import PlanNode
from propercode.models.agents.node_outputs import ContextNodeOutput

@dataclass
class ContextNode(BaseNode[AgentState,None,str]): # base node tells we need only AgentState as memory and outputs str
    '''
    Gathers information about the current project and stores in context
    '''
    context_agent : Agent[Any,ContextNodeOutput] = field(
        default_factory= lambda: Agent(
        model=None,
        system_prompt=CONTEXT_SYSTEM_PROMPT,
        output_type=ContextNodeOutput,
        retries=2,
        model_settings=ModelSettings(temperature=0.0),
        tools = [],
        )
    )

    async def run(self,ctx:GraphRunContext[AgentState]) -> PlanNode:
        try:
            if ctx.state.conversation_history is not None:
                ctx.state.conversation_history.append(f"User requested: {ctx.state.user_prompt}")
            
            self.context_agent.model = ctx.state.chat_model
            prompt = f"""User Request: '{ctx.state.user_prompt}'\nBased on the user's request, search your memory and read the relevant files to gather the best context for this task."""
            result = await self.context_agent.run(prompt)
            ctx.state.context_output = result.output
            print("[bold]Context Agent :[/bold]")
            print(f"[dim]Thoughts:\n{result.output.thought}[/dim]")
            return PlanNode()
        except Exception as e:
            raise e