import json
import os
from datetime import datetime
import click
import git
from openai import OpenAI

system_instruction = "You are going to work as a text generator, **you don't talk at all**, you will print your response in plain text without code block."

changelog_prompt = """
I have a `git diff` output from my recent code changes, and I need help with a changelog written in [insert_language]. 

## Changes
```diff
[insert_diff]
```

All notable changes to this project will be documented in this log.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Template:
```md
# Changelog

## [Version x.x.x] - [insert_date]

[write a detailed overview here.]

### Added(If applicable)
- [List new features that have been added.]
- [Include details about new modules, UI enhancements, etc.]

### Changed(If applicable)
- [Describe any changes to existing functionality.]
- [Note improvements, restructurings, or changes in behavior.]

### Deprecated(If applicable)
- [Document any features that are still available but are not recommended for use and will be removed in future versions.]

### Removed(If applicable)
- [List features or components that have been removed from this version.]

### Fixed(If applicable)
- [Highlight fixed bugs or issues.]
- [Include references to any tickets or bug report IDs if applicable.]

### Security(If applicable)
- [Mention any security improvements or vulnerabilities addressed in this version.]
```md
"""

@click.command()
@click.option('--lang', '-l', default=None, help='Target language for the generated changelog.')
@click.option('--model', '-m', default=None, help='The model to use for generating the changelog.')
@click.option('--max-tokens', '-t', type=int, help='The maximum number of tokens to use for the changelog.')
@click.option('--commit-range', '-r', type=int, help='The number of commits to include in the diff.')
def changelog(lang, model, max_tokens, commit_range):
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

    max_tokens = max_tokens or config.get('changelog_max_tokens', 2000)

    base_url = config.get('base', 'https://api.openai.com')
    client = OpenAI(api_key=config['api_key'], base_url=f"{base_url}")

    click.echo(f"Generating changelog using {model} in {lang}...")

    prompt = changelog_prompt.replace('[insert_diff]', diff).replace('[insert_language]', lang).replace('[insert_date]', datetime.now().strftime('%Y-%m-%d'))

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
    changelog_result = response['choices'][0]['message']['content'].strip()

    click.echo(f"Changelog generated successfully:\n\n{changelog_result}")