import os
from pathlib import Path
from yaml import dump,safe_load,YAMLError
from propercode.models.cli_config import CLISettings

CONFIG_DIR = Path.cwd() / ".propercode"
CONFIG_FILE = CONFIG_DIR / "propercode.yaml"

class ConfigManager:
    def __init__(self,config_file:Path=CONFIG_FILE):
        self.config_file = Path(config_file)
        self.settings = CLISettings()
        self.load()

    def load(self) -> CLISettings:
        '''
        loads the CLI settings
        '''
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        file_config = {}
        try:
            with self.config_file.open('r') as file:
                loaded_yaml = safe_load(file)
                if isinstance(loaded_yaml,dict):
                    file_config = loaded_yaml
        except (FileNotFoundError,YAMLError):
            pass

        self.settings = CLISettings(**file_config)

        if provider_env := os.getenv("PROPERCODE_PROVIDER"):
            self.settings.default_provider = provider_env
        if model_env := os.getenv("PROPERCODE_MODEL"):
            self.settings.default_model = model_env
        if verbose_env := os.getenv("PROPERCODE_VERBOSE"):
            self.settings.verbose = verbose_env.lower() in ['true','1','yes']

        return self.settings
    
    def save(self):
        '''
        Saves the current settings
        '''
        self.config_file.parent.mkdir(parents=True,exist_ok=True)
        config_data = self.settings.model_dump(exclude_defaults=False)
        with self.config_file.open('w') as write_file:
            dump(config_data,write_file,default_flow_style=False)
        
    
    def get_settings(self) -> CLISettings:
        '''
        Returns the current, loaded settings
        '''
        return self.settings