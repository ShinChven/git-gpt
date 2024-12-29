import click
import git
from .config_command import get_config
import os
from .ai_client import AIClient

system_instruction = "You are going to work as a text generator, **you don't talk at all**, you will print your response in plain text without code block."

quality_prompt = """I have a `git diff` output from my recent code changes, and I need help with a quality check report written in [insert_language]. 

## Changes
```diff
[insert_diff]
```

## Requirements:
1. Code Consistency: Please analyze if the changes are consistent with the existing coding style and standards in the project.
2. Potential Bugs: Highlight any lines in the diff that might introduce bugs or logical errors.
3. Best Practices: Suggest any improvements or best practices that could be applied to the changes.
4. Documentation and Comments: Check if the new code is adequately commented and if any documentation needs to be updated.
5. Performance Implications: Evaluate if there are any changes that might adversely affect the performance of the code.
6. Security Check: Examine the code for potential security vulnerabilities, such as SQL injection, cross-site scripting, data leaks, or any other security risks.
"""

@click.command()
@click.option('--lang', '-l', default=None, help='Target language for the generated message.')
@click.option('--model', '-m', default=None, help='The model to use for generating the quality check.')
@click.option('--max-tokens', '-t', type=int, help='The maximum number of tokens to use for the quality check.')
@click.option('--commit-range', '-r', type=int, help='The number of commits to include in the diff.')
def quality(lang, model, max_tokens, commit_range):
    config = get_config()

    lang = lang or config.get('lang', 'English')
    model = model or config.get('default_model')

    if not model:
        raise ValueError("No default model specified in configuration. Please run git-gpt set-default to set default model or run git-gpt config to add model configuration.")

    repo = git.Repo(os.getcwd())
    diff = repo.git.diff(f'HEAD~{commit_range or 1}..HEAD')

    max_tokens = max_tokens or config.get('quality_check_max_tokens', 2000)

    ai_client = AIClient(config)

    try:
        click.echo(f"Performing quality check using {model} in {lang}...")

        prompt = quality_prompt.replace('[insert_diff]', diff).replace('[insert_language]', lang)

        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt}
        ]

        response = ai_client.request(messages=messages, model_alias=model, max_tokens=max_tokens)
        quality_check_result = response
        click.echo(f"Quality check performed successfully:\n\n{quality_check_result}")
    except ValueError as e:
        click.echo(f"Error: {str(e)}")
        click.echo("Please make sure you have set the API key using `git-gpt config --api-key <API_KEY>`")
    except Exception as e:
        click.echo(f"Error performing quality check: {str(e)}")
        click.echo("Please check the ai_client.py file for more details on the error.")