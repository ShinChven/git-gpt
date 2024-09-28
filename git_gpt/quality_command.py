import json
import os
import click
import git
from openai import OpenAI

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

    lang = lang or config.get('lang', 'English')
    model = model or config.get('model', 'gpt-4o-mini')

    repo = git.Repo(os.getcwd())
    diff = repo.git.diff(f'HEAD~{commit_range or 1}..HEAD')

    max_tokens = max_tokens or config.get('quality_check_max_tokens', 2000)

    base_url = config.get('base', 'https://api.openai.com')
    client = OpenAI(api_key=config['api_key'], base_url=f"{base_url}")

    click.echo(f"Performing quality check using {model} in {lang}...")

    prompt = quality_prompt.replace('[insert_diff]', diff).replace('[insert_language]', lang)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt}
        ],
        max_tokens=max_tokens,
        stop=None
    )

    response = json.loads(response.model_dump_json())
    quality_check_result = response['choices'][0]['message']['content'].strip()

    click.echo(f"Quality check performed successfully:\n\n{quality_check_result}")