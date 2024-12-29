import json
import os
import click
from pathlib import Path
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.shortcuts import PromptSession
from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.layout import Layout

CONFIG_PATH = os.path.expanduser('~/.config/git-gpt/config.json')

def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r') as config_file:
            config = json.load(config_file)
    else:
        config = {"default_model": "", "models": {}}
    
    # Ensure 'default_model' and 'models' keys are always present
    if 'default_model' not in config:
        config['default_model'] = ""
    if 'models' not in config:
        config['models'] = {}
    
    return config

def save_config(config_data):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, 'w') as config_file:
        json.dump(config_data, config_file, indent=4, sort_keys=True)

def get_config():
    return load_config()

def select_from_list(options, default_index=0):
    selected_index = [default_index]
    
    def get_formatted_options():
        return [
            ("", f"{' > ' if i == selected_index[0] else '   '}{option}\n")
            for i, option in enumerate(options)
        ]

    kb = KeyBindings()

    @kb.add('up')
    def _(event):
        selected_index[0] = (selected_index[0] - 1) % len(options)

    @kb.add('down')
    def _(event):
        selected_index[0] = (selected_index[0] + 1) % len(options)

    @kb.add('enter')
    def _(event):
        event.app.exit(result=options[selected_index[0]])

    text_control = FormattedTextControl(get_formatted_options)
    window = Window(content=text_control)
    layout = Layout(window)

    application = Application(
        layout=layout,
        key_bindings=kb,
        mouse_support=True,
        full_screen=False,
    )

    result = application.run()
    return result

def update_config(alias, model_name, provider, key, api_base):
    config = get_config()
    
    if not alias:
        alias = prompt("Enter model alias: ")
    
    if not provider:
        provider_options = ['openai', 'azure-openai', 'ollama', 'claude', 'google-generativeai']
        print("Select provider (use up/down arrows and press Enter to select):")
        provider = select_from_list(provider_options)
        print(f"Selected provider: {provider}")

    if not model_name:
        if provider == 'azure-openai':
            model_name = prompt("Enter model name with Azure deployment: ")
        elif provider == 'claude':
            model_name = prompt("Enter Claude model name (e.g., claude-3-sonnet-20240229): ")
        elif provider == 'google-generativeai':
            model_name = prompt("Enter Google Generative AI model name (e.g., gemini-1.5-pro): ")
        else:
            model_name = prompt("Enter model name: ")
    
    if key is None:
        key = prompt("Enter API key (optional, press Enter to skip): ", default="")
    
    if api_base is None:
        if provider == 'claude':
            api_base = prompt("Enter API base URL (optional, default is https://api.anthropic.com): ", default="https://api.anthropic.com")
        elif provider == 'google-generativeai':
            api_base = prompt("Enter API base URL (optional, press Enter to skip): ", default="")
        else:
            api_base = prompt("Enter API base URL (optional, press Enter to skip): ", default="")
    
    if alias in config['models']:
        overwrite = prompt(f"Model alias '{alias}' already exists. Do you want to overwrite it? (y/n): ").lower()
        if overwrite != 'y':
            print("Configuration update cancelled.")
            return
    
    config['models'][alias] = {
        "model_name": model_name,
        "provider": provider,
        "key": key,
        "api_base": api_base
    }
    
    if not config['default_model']:
        config['default_model'] = alias
    
    save_config(config)
    
    set_default = prompt("Do you want to set this model as default? (y/N): ").lower()
    if set_default == 'y':
        set_default_model(alias)
    
    print(f"Configuration updated for model alias '{alias}'")

def set_default_model(alias):
    config = get_config()
    if not alias:
        available_aliases = list(config['models'].keys())
        if not available_aliases:
            raise click.ClickException("No models available to set as default.")
        default_index = available_aliases.index(config['default_model']) if config['default_model'] in available_aliases else 0
        print("Select a model alias to set as default (use up/down arrows and press Enter to select):")
        alias = select_from_list(available_aliases, default_index=default_index)

    if alias not in config['models']:
        raise click.ClickException(f"Error: Model alias '{alias}' not found in configuration.")
    
    config['default_model'] = alias
    save_config(config)
    click.echo(f"Default model set to '{alias}'")

def delete_config_command(alias):
    """Delete a model configuration by alias."""
    config = get_config()
    
    if not alias:
        available_aliases = list(config['models'].keys())
        if not available_aliases:
            click.echo("No models available to delete.", err=True)
            return
        print("Select a model alias to delete (use up/down arrows and press Enter to select):")
        alias = select_from_list(available_aliases)
    
    if alias in config['models']:
        model_config = config['models'][alias]

        # Mask the API key
        masked_key = model_config['key'][:2] + "*" * (len(model_config['key']) - 4) + model_config['key'][-2:]

        click.echo(f"Configuration for alias '{alias}':")
        click.echo(f"  Model Name: {model_config['model_name']}")
        click.echo(f"  Provider: {model_config['provider']}")
        click.echo(f"  API Key: {masked_key}")
        click.echo(f"  API Base: {model_config['api_base']}")

        if click.confirm("Are you sure you want to delete this configuration?"):
            del config['models'][alias]
            save_config(config)
            click.echo(f"Configuration for alias '{alias}' has been deleted.")
        else:
            click.echo("Deletion cancelled.")
    else:
        click.echo(f"Error: No configuration found for alias '{alias}'", err=True)

def show_models_command():
    """Show all models with their provider and masked key."""
    config = get_config()
    if not config['models']:
        click.echo("No models configured.", err=True)
        return

    click.echo("Configured models:\n")
    for alias, model_config in config['models'].items():
        masked_key = model_config['key'][:2] + "*" * (len(model_config['key']) - 4) + model_config['key'][-2:]
        click.echo(f"- Alias: {alias}")
        click.echo(f"  Model Name: {model_config['model_name']}")
        click.echo(f"  Provider: {model_config['provider']}")
        click.echo(f"  API Key: {masked_key}")
        click.echo(f"  API Base: {model_config['api_base']}")
        click.echo("")  # Blank line for better readability

@click.command(help="Configure a new model or update an existing one.")
@click.option('-a', '--alias', help='Model alias')
@click.option('-m', '--model_name', help='Model name')
@click.option('-p', '--provider', help='Provider name')
@click.option('-k', '--key', help='API key')
@click.option('-b', '--api_base', help='API base URL')
def config(alias, model_name, provider, key, api_base):
    try:
        update_config(alias, model_name, provider, key, api_base)
    except click.Abort:
        click.echo("Configuration cancelled.")
    except Exception as e:
        click.echo(f"Error updating configuration: {str(e)}", err=True)