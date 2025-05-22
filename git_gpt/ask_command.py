import click
import git
from .config_command import get_config
import os
from .ai_client import AIClient
from .git_diff import get_git_diff

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
    model = model or config.get('default_model')

    if not model:
        raise ValueError("No default model specified in configuration. Please run git-gpt set-default to set default model or run git-gpt config to add model configuration.")

    diff = get_git_diff(commit_range)

    ai_client = AIClient(config)

    try:
        click.echo(f"Generating answer using {model}...")

        prompt = ask_prompt.replace('[insert_diff]', diff).replace('[insert_question]', question)

        messages = [
            {"role": "system", "content": "You are a helpful code assistant, you will help users with their code, you will reply users in their language."},
            {"role": "user", "content": prompt}
        ]

        response = ai_client.request(messages=messages, model_alias=model)
        ask_result = response
        click.echo(f"Answer generated successfully:\n\n{ask_result}")
    except ValueError as e:
        click.echo(f"Error: {str(e)}")
        click.echo("Please make sure you have set the API key using `git-gpt config --api-key <API_KEY>`")
    except Exception as e:
        click.echo(f"Error generating answer: {str(e)}")
        click.echo("Please check the ai_client.py file for more details on the error.")
