import subprocess
import tempfile
import click
import openai
import git
import json
import os


@click.group()
def cli():
    pass

@cli.command(help=f"Configure the CLI. Configuration will be saved to {os.path.expanduser('~/.config/git-gpt/config.json')}")
@click.option('--api-key', help='The API key to use with OpenAI.')
@click.option('--host', help='The alternative OpenAI host.')
@click.option('--max-tokens', type=int, help='Maximum number of tokens for the generated message.')
@click.option('--lang', help='Target language for the generated message.')
def config(api_key, host, max_tokens, lang):
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
    if host:
        config_data['openai_host'] = host
    if max_tokens:
        config_data['max_tokens'] = max_tokens
    if lang:
        config_data['lang'] = lang

    # Save updated configuration with formatting
    with open(config_path, 'w') as config_file:
        json.dump(config_data, config_file, indent=4, sort_keys=True)
    
    # Output message indicating the location of the config file
    click.echo(f'Configuration saved to: {config_path}')


@cli.command()
@click.option('--max-tokens', default=None, help='Maximum number of tokens for the generated message.')
@click.option('--lang', default=None, help='Target language for the generated message.')
def commit(max_tokens, lang):
    config_path = os.path.expanduser('~/.config/git-gpt/config.json')
    with open(config_path, 'r') as config_file:
        config = json.load(config_file)

    # If arguments are not provided via command line, try to get them from the config file
    max_tokens = max_tokens or config.get('max_tokens', 100)
    lang = lang or config.get('lang', 'en')

    repo = git.Repo(os.getcwd())
    # add all changes to staged
    repo.git.add('--all')
    diffs = repo.git.diff('--staged')  # Get textual representation of staged diffs

    openai.api_key = config['api_key']
    openai.api_base = f"{config['openai_host']}/v1"

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": f"You are a senior programmer."},
            {"role": "user", "content": f"Generate a commit message for the following diffs with a message under 50 characters and Description under 72 characters, written in {lang}.\nThe message should start with `feat:` or `fix`. Please summarize the Description in a list.\n\ndiffs:\n{diffs}"}
        ],
        max_tokens=max_tokens,  # Using the max_tokens argument here
        stop=None
    )

    commit_message = response['choices'][0]['message']['content'].strip()
    
    # Create a temporary file to hold the commit message
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_file:
        temp_file.write(commit_message)
        temp_file_name = temp_file.name

    # Use git to open the commit message editing dialog
    try:
        subprocess.run(['git', 'commit', '-e', '-F', temp_file_name], check=True)
        click.echo("Commit created successfully.")
        click.echo("Please run `git amend` to edit the commit message.")
        click.echo("Or run `git reset HEAD~` to edit the commit message.")
    except subprocess.CalledProcessError:
        click.echo("Failed to create commit. Aborting.")
    finally:
        # Clean up the temporary file
        os.remove(temp_file_name)

@cli.command()
@click.option('--max-tokens', default=None, help='Maximum number of tokens for the generated message.')
@click.option('--lang', default=None, help='Target language for the generated message.')
def recommit(max_tokens, lang):
    config_path = os.path.expanduser('~/.config/git-gpt/config.json')
    with open(config_path, 'r') as config_file:
        config = json.load(config_file)

    # If arguments are not provided via command line, try to get them from the config file
    max_tokens = max_tokens or config.get('max_tokens', 100)
    lang = lang or config.get('lang', 'en')

    repo = git.Repo(os.getcwd())

    # reset commit
    repo.git.reset('HEAD~')

    # add all changes to staged
    repo.git.add('--all')
    diffs = repo.git.diff('--staged')  # Get textual representation of staged diffs

    openai.api_key = config['api_key']
    openai.api_base = f"{config['openai_host']}/v1"

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": f"You are a senior programmer."},
            {"role": "user", "content": f"Generate a commit message for the following diffs with a message under 50 characters and Description under 72 characters, written in {lang}.\nThe message should start with `feat:` or `fix`. Please summarize the Description in a list.\n\ndiffs:\n{diffs}"}
        ],
        max_tokens=max_tokens,  # Using the max_tokens argument here
        stop=None
    )

    commit_message = response['choices'][0]['message']['content'].strip()
    
    # Create a temporary file to hold the commit message
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_file:
        temp_file.write(commit_message)
        temp_file_name = temp_file.name

    # Use git to open the commit message editing dialog
    try:
        subprocess.run(['git', 'commit', '-e', '-F', temp_file_name], check=True)
        click.echo("Commit created successfully.")
        click.echo("Please run `git amend` to edit the commit message.")
        click.echo("Or run `git reset HEAD~` to edit the commit message.")
    except subprocess.CalledProcessError:
        click.echo("Failed to create commit. Aborting.")
    finally:
        # Clean up the temporary file
        os.remove(temp_file_name)

if __name__ == '__main__':
    cli()
