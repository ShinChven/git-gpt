import json
import os
import click

@click.command(help=f"Configure the CLI. Configuration will be saved to {os.path.expanduser('~/.config/git-gpt/config.json')}")
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

    # Save updated configuration with formatting
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    with open(config_path, 'w') as config_file:
        json.dump(config_data, config_file, indent=4, sort_keys=True)
    
    # Output message indicating the location of the config file
    click.echo(f'Configuration saved to: {config_path}')