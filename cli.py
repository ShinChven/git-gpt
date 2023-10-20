import json
import os

import click
import git
import openai
import requests


@click.group()
def cli():
    pass

@cli.command()
@click.option('--api-key', prompt='Your API key', help='The API key to use with OpenAI.')
@click.option('--host', prompt='OpenAI Host', help='The alternative OpenAI host.')
def config(api_key, host):
    config_path = os.path.expanduser('~/.config/git-gpt/config.json')
    with open(config_path, 'w') as config_file:
        json.dump({'api_key': api_key, 'openai_host': host}, config_file)


@cli.command()
def commit():
    config_path = os.path.expanduser('~/.config/git-gpt/config.json')
    with open(config_path, 'r') as config_file:
        config = json.load(config_file)

    repo = git.Repo(os.getcwd())
    diffs = repo.git.diff('--staged')  # Get textual representation of staged diffs

    openai.api_key = config['api_key']
    openai.api_base = f"{config['openai_host']}/v1"

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"Generate a detailed commit message for the following diffs.\n You should conclude a short message first, then explain the features in a list. here's the diffs:\n{diffs}"}
        ],
        max_tokens=100,
        stop=None
    )

    commit_message = response['choices'][0]['message']['content'].strip()
    print(commit_message)


if __name__ == '__main__':
    cli()
