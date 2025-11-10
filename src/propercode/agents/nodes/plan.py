from rich import print
from typing import Any
from dataclasses import dataclass,field
from pydantic_ai import Agent,ModelSettings
from pydantic_graph import BaseNode,GraphRunContext

from propercode.agents.nodes import PLAN_SYSTEM_PROMPT
from propercode.agents.memory.state import AgentState
from propercode.models.agents.node_outputs import PlanNodeOutput
from propercode.agents.nodes.code_eval import CodeNode

@dataclass
class PlanNode(BaseNode[AgentState, None, str]):
    plan_agent: Agent[Any,PlanNodeOutput] = field(
        default_factory=lambda: Agent(
        model=None,
        system_prompt=PLAN_SYSTEM_PROMPT,
        output_type=PlanNodeOutput,
        retries=3,
        model_settings=ModelSettings(temperature=0.3)
        )
    )

    async def run(self, ctx: GraphRunContext[AgentState]) -> CodeNode:
        try:
            if ctx.state.conversation_history is not None:
                ctx.state.conversation_history.append(f"Planning for: {ctx.state.user_prompt}")
                
            self.plan_agent.model = ctx.state.chat_model
            context = ctx.state.context_output.context if ctx.state.context_output else "No context available"
            thought = ctx.state.context_output.thought if ctx.state.context_output else "No reason available"
            
            prompt = f"""Here is the project context you must consider:\n{context}\nContextual reasoning:{thought}\n History: {ctx.state.conversation_history} Output a thought and 3-6 actionable steps"""

            result = await self.plan_agent.run(prompt)
            ctx.state.plan_output = result.output

            print("[bold]Plan Agent :[/bold]")
            print(f"[dim]Thoughts:\n{result.output.thought}[/dim]")

            return CodeNode()
        except Exception as e:
            raise e
