import json
import os
import click

CONFIG_PATH = os.path.expanduser('~/.config/git-gpt/config.json')

def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r') as config_file:
            return json.load(config_file)
    return {}

def save_config(config_data):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, 'w') as config_file:
        json.dump(config_data, config_file, indent=4, sort_keys=True)

@click.command(help=f"Configure the CLI. Configuration will be saved to {CONFIG_PATH}")
@click.option('--api-key', '-k', help='The API key to use with OpenAI.')
@click.option('--base', '-b', help='The alternative OpenAI host.')
@click.option('--model', '-m', help='The model to use for generating the commit message.')
@click.option('--lang', '-l', help='Target language for the generated message.')
@click.option('--max-tokens-quality', type=int, help='Maximum number of tokens for quality module responses.')
@click.option('--max-tokens-issue', type=int, help='Maximum number of tokens for issue module responses.')
@click.option('--max-tokens-changelog', type=int, help='Maximum number of tokens for changelog module responses.')
@click.option('--api-type', type=click.Choice(['openai', 'ollama']), help='The type of API to use (openai or ollama).')
@click.option('--ollama-base', help='The base URL for Ollama API.')
def config(api_key, base, model, lang, max_tokens_quality, max_tokens_issue, max_tokens_changelog, api_type, ollama_base):
    config_data = load_config()

    # Update configuration with provided arguments
    if api_key:
        config_data['api_key'] = api_key
    if base:
        config_data['base'] = base
    if model:
        config_data['model'] = model
    if lang:
        config_data['lang'] = lang
    if max_tokens_quality is not None:
        config_data['max_tokens_quality'] = max_tokens_quality
    if max_tokens_issue is not None:
        config_data['max_tokens_issue'] = max_tokens_issue
    if max_tokens_changelog is not None:
        config_data['max_tokens_changelog'] = max_tokens_changelog
    if api_type:
        config_data['api_type'] = api_type
    if ollama_base:
        config_data['ollama_base'] = ollama_base

    # Validate API type and base URL combinations
    if config_data.get('api_type') == 'openai' and 'base' not in config_data:
        config_data['base'] = 'https://api.openai.com'
    elif config_data.get('api_type') == 'ollama' and 'ollama_base' not in config_data:
        config_data['ollama_base'] = 'http://localhost:11434'

    save_config(config_data)
    
    click.echo(f'Configuration saved to: {CONFIG_PATH}')
    click.echo('Current configuration:')
    for key, value in config_data.items():
        if key != 'api_key':
            click.echo(f'{key}: {value}')
        else:
            click.echo(f'{key}: {"*" * len(value)}')  # Mask the API key

# This function can be imported and used in other command files
def get_config():
    return load_config()