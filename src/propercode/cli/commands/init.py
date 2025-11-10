import typer
from rich import print
from rich.prompt import Prompt

from propercode.cli.banner import BANNER
from propercode.cli.core.config import ConfigManager

app = typer.Typer(name="init",help="Initialize the Propercode in your system")

providers_and_models = {
    "openrouter":["minimax/minimax-m2:free","alibaba/tongyi-deepresearch-30b-a3b:free","openrouter/polaris-alpha","moonshotai/kimi-k2:free"],
}

@app.callback(invoke_without_command=True)
def init_callback():
    '''
    Initialize the propercode CLI tool
    '''
    print(BANNER)
    print("\n[bold]Let's get started[/bold]")

    config_manager = ConfigManager()
    current_settings = config_manager.get_settings()
    current_settings.default_provider = "openrouter"

    print("\n1. Select your preferred model : ")
    for i,model_name in enumerate(providers_and_models["openrouter"],1):
        print(f"\t{i}. {model_name}")

    provider_choice = Prompt.ask("\nEnter the number of your preferred provider",choices=[str(i) for i in range(1,len(providers_and_models["openrouter"])+1)],default="1")
    selected_model = providers_and_models["openrouter"][int(provider_choice) - 1]
    current_settings.default_model = selected_model

    print(f"\nYou've selected [bold]{selected_model}[/bold] as your default model")

    config_manager.save()
    print(f"\nEnter the [bold]propercode keys add[/bold]")