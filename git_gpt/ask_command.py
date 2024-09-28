import click
import git
from .request_module import RequestModule
from .config_command import get_config
import os

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
    config = get_config()

    if 'api_key' not in config:
        click.echo("API key not set. Please set the API key using `git-gpt config --api-key <API_KEY>`")
        return

    model = model or config.get('model', 'gpt-4o-mini')

    repo = git.Repo(os.getcwd())
    diff = repo.git.diff(f'HEAD~{commit_range or 1}..HEAD')

    request_module = RequestModule(config)

    click.echo(f"Generating answer using {model}...")

    prompt = ask_prompt.replace('[insert_diff]', diff).replace('[insert_question]', question)

    messages = [
        {"role": "system", "content": "You are a helpful code assistant, you will help users with their code, you will reply users in their language."},
        {"role": "user", "content": prompt}
    ]

    try:
        response = request_module.send_request(messages=messages, model=model, temperature=0.7)
        ask_result = request_module.get_response_content(response)
        click.echo(f"Answer generated successfully:\n\n{ask_result}")
    except Exception as e:
        click.echo(f"Error generating answer: {str(e)}")
        click.echo("Please check the request_module.py file for more details on the error.")