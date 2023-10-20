import json
import os
import subprocess
import tempfile

import click
import git
import openai


@click.group()
def cli():
    pass

@cli.command(help=f"Configure the CLI. Configuration will be saved to {os.path.expanduser('~/.config/git-gpt/config.json')}")
@click.option('--api-key', help='The API key to use with OpenAI.')
@click.option('--base', help='The alternative OpenAI host.')
@click.option('--lang', help='Target language for the generated message.')
@click.option('--issue-max-tokens', type=int, help='The maximum number of tokens to use for the issue prompt.')
def config(api_key, base, lang, issue_max_tokens):
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
    if lang:
        config_data['lang'] = lang
    if issue_max_tokens:
        config_data['issue_max_tokens'] = issue_max_tokens

    # Save updated configuration with formatting
    with open(config_path, 'w') as config_file:
        json.dump(config_data, config_file, indent=4, sort_keys=True)
    
    # Output message indicating the location of the config file
    click.echo(f'Configuration saved to: {config_path}')


@cli.command()
@click.option('--lang', default=None, help='Target language for the generated message.')
def commit(lang):
    config_path = os.path.expanduser('~/.config/git-gpt/config.json')
    if not os.path.exists(config_path):
        # Create the parent directory if it does not exist
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        # Create the config file with an empty dictionary
        with open(config_path, 'w') as config_file:
            json.dump({}, config_file)

    with open(config_path, 'r') as config_file:
        config = json.load(config_file)

    if 'api_key' not in config:
        print("API key not set. Please set the API key in the config file at ~/.config/git-gpt/config.json")
        print('You can config the API key by running `git-gpt config --api-key <API_KEY>`')
        return

    # If arguments are not provided via command line, try to get them from the config file
    lang = lang or config.get('lang', 'en')

    repo = git.Repo(os.getcwd())
    # add all changes to staged
    repo.git.add('--all')
    diffs = repo.git.diff('--staged')  # Get textual representation of staged diffs

    openai.api_key = config['api_key']
    if 'base' in config:
        openai.api_base = f"{config['base']}/v1"

    # print loading animation
    click.echo("Generating commit message...")

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": f"You are a senior programmer."},
            {"role": "user", "content": f"Generate a commit message for the following diffs with a message under 50 characters and Description under 72 characters, written in {lang}.\nThe message should start with `feat:` or `fix`. Please summarize the Description in a list.\n\ndiffs:\n{diffs}"}
        ],
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
@click.option('--lang', default=None, help='Target language for the generated message.')
@click.option('--max-tokens', type=int, help='The maximum number of tokens to use for the issue prompt.')
def issue(lang, max_tokens):
    config_path = os.path.expanduser('~/.config/git-gpt/config.json')
    if not os.path.exists(config_path):
        # Create the parent directory if it does not exist
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        # Create the config file with an empty dictionary
        with open(config_path, 'w') as config_file:
            json.dump({}, config_file)

    with open(config_path, 'r') as config_file:
        config = json.load(config_file)

    if 'api_key' not in config:
        print("API key not set. Please set the API key in the config file at ~/.config/git-gpt/config.json")
        print('You can config the API key by running `git-gpt config --api-key <API_KEY>`')
        return

    # If arguments are not provided via command line, try to get them from the config file
    lang = lang or config.get('lang', 'en')

    repo = git.Repo(os.getcwd())
    # read the diffs of the latest commit
    diffs = repo.git.diff('HEAD~1..HEAD')  # Get textual representation of staged diffs

    # if max tokens is not provided, use the default value
    max_tokens = max_tokens or config.get('issue_max_tokens', 1000)

    openai.api_key = config['api_key']
    if 'base' in config:
        openai.api_base = f"{config['base']}/v1"

    # print loading animation
    click.echo("Generating issue...")

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": f"You are a senior programmer."},
            {"role": "user", "content": f"Please write a development issue to introduce target and tasks according to the following diffs in {lang}:\n{diffs}"}
        ],
        max_tokens=max_tokens,
        stop=None
    )

    issue = response['choices'][0]['message']['content'].strip()
    
    click.echo(f"Issue created successfully:\n{issue}")


if __name__ == '__main__':
    cli()
