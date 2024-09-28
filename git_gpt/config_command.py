import json
import os
import click

@click.command(help=f"Configure the CLI. Configuration will be saved to {os.path.expanduser('~/.config/git-gpt/config.json')}")
@click.option('--api-key', '-k', help='The API key to use with OpenAI.')
@click.option('--base', '-b', help='The alternative OpenAI host.')
@click.option('--model', '-m', help='The model to use for generating the commit message.')
@click.option('--lang', '-l', help='Target language for the generated message.')
def config(api_key, base, model, lang):
    config_path = os.path.expanduser('~/.config/git-gpt/config.json')
    
    # Load existing configuration if it exists
    if os.path.exists(config_path):
        with open(config_path, 'r') as config_file:
            config_data = json.load(config_file)
    else:
        config_data = {}

    # Update configuration with provided arguments
    if api_key:
        config_data['api_key'] = api_key
    if base:
        config_data['base'] = base
    if model:
        config_data['model'] = model
    if lang:
        config_data['lang'] = lang

    # Save updated configuration with formatting
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    with open(config_path, 'w') as config_file:
        json.dump(config_data, config_file, indent=4, sort_keys=True)
    
    # Output message indicating the location of the config file
    click.echo(f'Configuration saved to: {config_path}')