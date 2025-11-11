import typer
from rich import print

from propercode.cli.core.config import ConfigManager

from .commands.init import app as init_app
from .commands.keys import app as keys_app
from .commands.run import app as run_app

from .commands.stats import app as stats_app

app = typer.Typer(name="propercode",help="AI Agentic Coding Tool",rich_markup_mode="markdown",no_args_is_help=True)

@app.callback()
def main_callback(ctx:typer.Context,help="The specific model to use. Overrides configs"):
    '''
    Main callback to manage global state and options
    '''
    state_manager = ConfigManager()
    settings = state_manager.get_settings()
    
    ctx.obj = settings

app.add_typer(init_app,name="init")
app.add_typer(keys_app,name="keys")
app.add_typer(run_app,name="run")
app.add_typer(stats_app,name="stats")

def main():
    '''
    Entry point of the CLI tool
    '''
    try:
        app()
    except (KeyboardInterrupt,EOFError) as _:
        print("[bold]Exiting[/bold]")
        raise typer.Exit()