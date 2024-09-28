from datetime import datetime
import click
import git
from .request_module import RequestModule
from .config_command import get_config

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
    config = get_config()

    if 'api_key' not in config:
        click.echo("API key not set. Please set the API key using `git-gpt config --api-key <API_KEY>`")
        return

    lang = lang or config.get('lang', 'English')
    model = model or config.get('model', 'gpt-4o-mini')

    repo = git.Repo(os.getcwd())
    diff = repo.git.diff(f'HEAD~{commit_range or 1}..HEAD')

    max_tokens = max_tokens or config.get('changelog_max_tokens', 2000)

    request_module = RequestModule(config)

    click.echo(f"Generating changelog using {model} in {lang}...")

    prompt = changelog_prompt.replace('[insert_diff]', diff).replace('[insert_language]', lang).replace('[insert_date]', datetime.now().strftime('%Y-%m-%d'))

    messages = [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": prompt}
    ]

    try:
        response = request_module.send_request(messages=messages, model=model, temperature=0.7)
        changelog_result = request_module.get_response_content(response)
        click.echo(f"Changelog generated successfully:\n\n{changelog_result}")
    except Exception as e:
        click.echo(f"Error generating changelog: {str(e)}")
        click.echo("Please check the request_module.py file for more details on the error.")