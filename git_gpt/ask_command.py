import json
import os
import click
import git
from openai import OpenAI

ask_prompt = """
```diff
[insert_diff]
```
[insert_question]
"""

@click.command()
@click.option('--model', '-m', default=None, help='The model to use for generating the answer.')
@click.option('--commit-range', '-r', type=int, help='The number of commits to include in the diff.')
@click.option('--question', '-q', help='The question to ask.', required=True)
def ask(model, commit_range, question):
    config_path = os.path.expanduser('~/.config/git-gpt/config.json')
    if not os.path.exists(config_path):
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w') as config_file:
            json.dump({}, config_file)

    with open(config_path, 'r') as config_file:
        config = json.load(config_file)

    if 'api_key' not in config:
        print("API key not set. Please set the API key in the config file at ~/.config/git-gpt/config.json")
        print('You can config the API key by running `git-gpt config --api-key <API_KEY>`')
        return

    model = model or config.get('model', 'gpt-4o-mini')

    repo = git.Repo(os.getcwd())
    diff = repo.git.diff(f'HEAD~{commit_range or 1}..HEAD')

    base_url = config.get('base', 'https://api.openai.com')
    client = OpenAI(api_key=config['api_key'], base_url=f"{base_url}")

    click.echo(f"Generating answer using {model}...")

    prompt = ask_prompt.replace('[insert_diff]', diff).replace('[insert_question]', question)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful code assistant, you will help users with their code, you will reply users in their language."},
            {"role": "user", "content": prompt}
        ],
        stop=None
    )

    response = json.loads(response.model_dump_json())
    ask_result = response['choices'][0]['message']['content'].strip()

    click.echo(f"Answer generated successfully:\n\n{ask_result}")