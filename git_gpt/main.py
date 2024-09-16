import json
import os
import subprocess
import tempfile
from datetime import datetime

import click
import git
from openai import OpenAI

from git_gpt import __version__

default_model = 'gpt-4o-mini'

@click.group()
@click.version_option(version=__version__, prog_name='git-gpt')
def cli():
    pass

@cli.command(help=f"Configure the CLI. Configuration will be saved to {os.path.expanduser('~/.config/git-gpt/config.json')}")
@click.option('--api-key', '-k', help='The API key to use with OpenAI.')
@click.option('--base', '-b', help='The alternative OpenAI host.')
@click.option('--model', '-m', help='The model to use for generating the commit message.')
@click.option('--lang', '-l', help='Target language for the generated message.')
@click.option('--issue-max-tokens', type=int, help='The maximum number of tokens to use for the issue command.')
@click.option('--changelog-max-tokens', type=int, help='The maximum number of tokens to use for the changelog command.')
@click.option('--quality-check-max-tokens', type=int, help='The maximum number of tokens to use for the quality check command.')
def config(api_key, base, model, lang, issue_max_tokens, changelog_max_tokens, quality_check_max_tokens):
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
    if model:
        config_data['model'] = model
    if lang:
        config_data['lang'] = lang
    if issue_max_tokens:
        config_data['issue_max_tokens'] = issue_max_tokens

    # Save updated configuration with formatting
    with open(config_path, 'w') as config_file:
        json.dump(config_data, config_file, indent=4, sort_keys=True)
    
    # Output message indicating the location of the config file
    click.echo(f'Configuration saved to: {config_path}')


system_instruction = "You are going to work as a text generator, **you don't talk at all**, you will print your response in plain text without code block."

# https://www.conventionalcommits.org/en/v1.0.0/
commit_message_prompt = f"""You are going to work as commit message generator, you will print the message without code block, and **You don't talk**.

Please analyze staged diffs:
```diff
[insert_diff]
```
Then, craft a conventional commit message a title under 50 characters and a list of details about changes under 70 characters to describe the commit in [insert_language]. 
Use appropriate type (e.g., 'feat:', 'fix:', 'docs:', 'style:', 'refactor:', 'test:', 'chore:', etc.). 

Here's the required format of the commit message

```txt
<type>[optional scope]: <title>

Added(If applicable):
- [List new features that have been added.]
- [Include details about new modules, UI enhancements, etc.]

Changed(If applicable):
- [Describe any changes to existing functionality.]
- [Note improvements, restructurings, or changes in behavior.]

Deprecated(If applicable):
- [Document any features that are still available but are not recommended for use and will be removed in future versions.]

Removed(If applicable):
- [List features or components that have been removed from this version.]

Fixed(If applicable):
- [Highlight fixed bugs or issues.]
- [Include references to any tickets or bug report IDs if applicable.]

Security(If applicable):
- [Mention any security improvements or vulnerabilities addressed in this version.]

```
"""


@cli.command()
@click.option('--lang', '-l', default=None, help='Target language for the generated message.')
@click.option('--model', '-m', default=None, help='The model to use for generating the commit message.')
@click.option('--run-dry', '-d', is_flag=True, help='Run the command to print the commit message without actually committing.')
def commit(lang, model, run_dry):
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
    lang = lang or config.get('lang', 'English')
    model = model or config.get('model', 'gpt-4o-mini')

    repo = git.Repo(os.getcwd())
    # add all changes to staged
    repo.git.add('--all')
    diff = repo.git.diff('--staged')  # Get textual representation of staged diffs

    base_url = config.get('base', 'https://api.openai.com')

    client = OpenAI(api_key=config['api_key'], base_url=f"{base_url}")

    # print loading animation
    click.echo(f"Generating commit message with {model} in {lang}...")

    prompt = commit_message_prompt

    # replace [insert_diff] with the actual diffs
    prompt = prompt.replace('[insert_diff]', diff)
    # replace [insert_language] with the target language
    prompt = prompt.replace('[insert_language]', lang)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt}
        ],
        max_tokens=200,
        stop=None
    )

    response = json.loads(response.model_dump_json())
    commit_message = response['choices'][0]['message']['content'].strip()

    if run_dry:
        click.echo(f"Commit message generated successfully:\n\n{commit_message}")
        return
    
    # Create a temporary file to hold the commit message
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_file:
        temp_file.write(f"# Generated by git-gpt\n\n{commit_message}")
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


issue_prompt = """You will work as a GitHub issue generator, and **you don't talk**, you will print the content in plain text without code block.
Please generate a development issue according in [insert_language] to the changes below:
```diff
[insert_diff]
```

Issue template:

## [Brief description of the feature or bug]

## Description
[Provide a detailed description of the feature to be implemented or the bug to be fixed]

## Requirements
- [ ] Requirement 1
- [ ] Requirement 2
- [ ] Requirement 3
- [ ] ...

## Acceptance Criteria
- [ ] Criteria 1
- [ ] Criteria 2
- [ ] Criteria 3
- [ ] ...

## Technical Details
[Provide any technical specifications, API endpoints, data models, etc.]

## Dependencies
- [List any dependencies or related issues]

## Mockups/Screenshots
[If applicable, include mockups or screenshots]

## Additional Information
[Any other relevant information, context, or resources]

## Estimated Effort
[Provide an estimate of the expected effort, e.g., story points or time]

## Priority
[Set the priority level: Low/Medium/High/Critical]

## Assigned To
[Name of the person assigned to this task]

## Labels
[Add relevant labels, e.g., "feature", "bug", "enhancement"]

## Milestone
[If applicable, link to the relevant milestone]

"""

@cli.command()
@click.option('--lang', '-l', default=None, help='Target language for the generated message.')
@click.option('--model', '-m', default=None, help='The model to use for generating the commit message.')
@click.option('--max-tokens', '-t', type=int, help='The maximum number of tokens to use for the issue prompt.')
@click.option('--commit-range', '-r', type=int, help='The maximum number of tokens to use for the issue prompt.')
def issue(lang, model, max_tokens, commit_range):
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
    lang = lang or config.get('lang', 'English')
    model = model or config.get('model', default_model)

    repo = git.Repo(os.getcwd())
    # read the diffs of the latest commit
    diff = repo.git.diff(f'HEAD~{commit_range or 1}..HEAD')  # Get textual representation of staged diffs

    # if max tokens is not provided, use the default value
    max_tokens = max_tokens or config.get('issue_max_tokens', 2000)

    base_url = config.get('base', 'https://api.openai.com')
    client = OpenAI(api_key=config['api_key'], base_url=f"{base_url}")

    # print loading animation
    click.echo(f"Generating issue using {model} in {lang}...")

    prompt = issue_prompt.replace('[insert_diff]', diff).replace('[insert_language]', lang)

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

    issue = response['choices'][0]['message']['content'].strip()
    
    click.echo(f"Issue created successfully:\n\n{issue}")


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

@cli.command()
@click.option('--lang', '-l', default=None, help='Target language for the generated message.')
@click.option('--model', '-m', default=None, help='The model to use for generating the quality check.')
@click.option('--max-tokens', '-t', type=int, help='The maximum number of tokens to use for the quality check.')
@click.option('--commit-range', '-r', type=int, help='The maximum number of tokens to use for the quality check.')
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
    model = model or config.get('model', default_model)

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


@cli.command()
@click.option('--lang', '-l', default=None, help='Target language for the generated changelog.')
@click.option('--model', '-m', default=None, help='The model to use for generating the changelog.')
@click.option('--max-tokens', '-t', type=int, help='The maximum number of tokens to use for the changelog.')
@click.option('--commit-range', '-r', type=int, help='The maximum number of tokens to use for the changelog.')
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
    model = model or config.get('model', default_model)

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

ask_prompt = """
```diff
[insert_diff]
```
[insert_question]
"""

@cli.command()
@click.option('--model', '-m', default=None, help='The model to use for generating the changelog.')
@click.option('--commit-range', '-r', type=int, help='The maximum number of tokens to use for the changelog.')
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

    model = model or config.get('model', default_model)
    question = question or config.get('question', '')

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

    click.echo(f"Changelog generated successfully:\n\n{ask_result}")


if __name__ == '__main__':
    cli()
