from pathlib import Path
import typer
from rich import print
from rich.panel import Panel
from rich.syntax import Syntax
from rich.console import Console
from rich.prompt import Confirm
import asyncio

from propercode.models.cli_config import CLISettings
from propercode.agents.orchestrator import CodeOrchestrator
from propercode.agents.memory.state import AgentState

app = typer.Typer(name="run",help="Allows you to perform single coding task",no_args_is_help=True)

def write_file(file_path:str,content:str):
    try:
        full_path = Path.cwd() / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        with full_path.open("w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        return f"Error writing file {file_path}: {e}"

@app.callback(invoke_without_command=True)
def run(ctx:typer.Context,prompt:str=typer.Argument(...,help="Provide the coding task for the agent to write code"),auto_apply: bool = typer.Option(False,"--auto-apply", "-a",help="Automatically apply the generated code after confirmation.")):
    settings : CLISettings = ctx.obj

    async def _async_run():
        print(Panel(f"🚀 Starting agent run for prompt: '[bold]{prompt}[/bold]'", title="[bold green]Propercode[/bold green]", border_style="green"))
        print(f"[dim]Using provider: {settings.default_provider}, model: {settings.default_model}[/dim]\n")

        orch = CodeOrchestrator(model_name=settings.default_model or "minimax/minimax-m2:free")
        state = AgentState(user_prompt=prompt, max_retries=2)
        output, final_state = await orch.run(state)

        print("Output:", output)
        print("Errors:", final_state.errors)
        syntax = Syntax(final_state.code_output.code if final_state.code_output else "#no code",final_state.code_output.code if final_state.code_output else "python",theme="monokai",line_numbers=True,word_wrap=True)
        console = Console()
        console.print(syntax)

        file_name = final_state.code_output.file_name if final_state.code_output else "genenerated.md"
        generated_code = final_state.code_output.code if final_state.code_output else ""

        if auto_apply:
            if Confirm.ask(f"\n[bold yellow]Do you want to apply this code to {file_name}?[/bold yellow]"):
                write_file(file_name, generated_code)
            else:
                print("Aborted. No changes were made.")
        else:
            print("\n[dim]To apply the code, re-run with the --auto-apply flag.[/dim]")
    
    asyncio.run(_async_run())