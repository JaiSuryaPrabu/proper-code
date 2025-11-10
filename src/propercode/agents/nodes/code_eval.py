from rich import print
from typing import Any,Union
from dataclasses import dataclass,field
from pydantic_ai import Agent,ModelSettings
from pydantic_graph import BaseNode,GraphRunContext
from pydantic_graph.nodes import End

from propercode.agents.nodes import CODE_SYSTEM_PROMPT,EVAL_SYSTEM_PROMPT
from propercode.agents.memory.state import AgentState
from propercode.models.agents.node_outputs import CodeNodeOutput,EvaluationNodeOutput,Verdict

@dataclass
class CodeNode(BaseNode[AgentState, None, str]):
    code_agent: Agent[Any,CodeNodeOutput] = field(
        default_factory=lambda: Agent(
        model=None,
        system_prompt=CODE_SYSTEM_PROMPT,
        output_type=CodeNodeOutput,
        retries=3,
        model_settings=ModelSettings(temperature=0.3)
        )
    )

    async def run(self, ctx: GraphRunContext[AgentState]) -> EvaluationNode:
        try:            
            self.code_agent.model = ctx.state.chat_model
            prior_feedback = ""
            if ctx.state.evaluation_output and ctx.state.evaluation_output.verdict == Verdict.FAIL:
                prior_feedback = f"Previous feedback: {ctx.state.evaluation.feedback}\nPrevious code:\n{ctx.state.code_output.code if ctx.state.code_output else ''}"

            prompt = f"""Implement code for: "{ctx.state.user_prompt}" Plan: {ctx.state.plan_output.plan if ctx.state.plan_output else 'No plan available'} Context: {ctx.state.context_output.context if ctx.state.context_output else ''} History: {ctx.state.conversation_history} {prior_feedback} Generate thought, code, filename and programming language.
            """
            result = await self.code_agent.run(prompt)
            ctx.state.code_output = result.output

            print("[bold]Code Agent:[/bold]")
            print(f"[dim]Thought: {result.output.thought}[/dim]")

            return EvaluationNode()
        except Exception as e:
            raise e
        
@dataclass
class EvaluationNode(BaseNode[AgentState, None, str]):
    eval_agent: Agent[Any,EvaluationNodeOutput] = field(
        default_factory=lambda: Agent(
            model=None,
            system_prompt=EVAL_SYSTEM_PROMPT,
            output_type=EvaluationNodeOutput,
            retries=3,
            model_settings=ModelSettings(temperature=0.2)
        )
    )

    async def run(self, ctx: GraphRunContext[AgentState]) -> Union[End[str],CodeNode]:
        try:
            self.eval_agent.model = ctx.state.chat_model  
            prompt=f"""Evaluate the code for: "{ctx.state.user_prompt}"Code to evaluate:\n{ctx.state.code_output.code if ctx.state.code_output else "Failed to fetch code"} Plan: {ctx.state.plan_output.plan if ctx.state.plan_output else ''} Context: {ctx.state.context_output.context if ctx.state.context_output else ''} History: {ctx.state.conversation_history} Provide thought, verdict (PASS/FAIL), and feedback if FAIL."""
            result = await self.eval_agent.run(prompt)
            ctx.state.evaluation_output = result.output

            print("[bold]Evaluation Agent :[/bold]")
            print(f"[dim]Thought: {result.output.thought}[/dim]")

            if result.output.verdict == Verdict.FAIL and ctx.state.retries < ctx.state.max_retries:
                ctx.state = ctx.state.increment_retries()
                ctx.state = ctx.state.append_history(f"Evaluator #{ctx.state.retries}: FAILED - {result.output.feedback}")
                return CodeNode()
            else:
                if result.output.verdict == Verdict.PASS:
                    ctx.state = ctx.state.append_history(f"Evaluator: PASS - {result.output.thought}")
                    return End("Task completed successfully!")
                else:
                    ctx.state = ctx.state.add_error("Max retries exceeded.")
                    return End("Failed after max retries.")
        except Exception as e:
            ctx.state = ctx.state.add_error(f"EvaluationNode failed: {e}")
            raise e