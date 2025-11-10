import os
import typer
from rich import print
from rich.prompt import Prompt
import keyring

service_name = "propercode"
app = typer.Typer(name="keys",help="Manage your keys by adding, removing API keys for specific providers and models and it also overwrite the existing key")

@app.command("add",help="Let's you add API keys")
def add_key():
    '''
    Add and store the API key in a secure way
    '''
    api_key = Prompt.ask("Please enter the API key",password=True)
    if not api_key:
        print("[bold]Failed to store the API key[/bold]")
        raise typer.Exit(code=1)
    
    try:
        keyring.set_password(service_name,"openrouter_api",api_key)
        print("[bold]API key has been stored successfully[/bold]")
    except Exception as e:
        print(f"[bold red]API key failed to store : {e}[/bold red]")

@app.command(name="delete",help="Let's you delete the stored API key")
def delete_key():
    '''
    Delete the stored API key
    '''
    try:
        keyring.delete_password(service_name,"openrouter_api")
        print("[bold]API key has been removed successfully[/bold]")
        print("[dim] Try 'propercode keys add' command to use our Agent")
    except Exception as e:
        print(f"[bold red]Failed to remove the API key: {e}[/bold red]")

def get_api_key(provider: str = "openrouter") -> str | None:
    """Helper to retrieve key with env fallback."""
    key = keyring.get_password(service_name, f"{provider}_api")
    if not key:
        key = os.getenv(f"PROPERCODE_{provider.upper()}_API_KEY")
        if key:
            print(f"[dim]Using env var fallback for {provider}[/dim]")
    return key

@app.command("get", help="Retrieve and print the stored API key (for testing)")
def get_key(
    provider: str = typer.Argument("openrouter", help="Provider (e.g., openrouter)")
):
    '''Debug: Print the key (be careful in shared envs!).'''
    key = get_api_key(provider)
    if key:
        print(f"[bold]{provider} API key: {key}[/bold]")
    else:
        print(f"[bold red]No {provider} API key found (check keyring or env var).[/bold red]")