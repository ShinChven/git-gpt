import json
import os
import subprocess
import tempfile

import click
import git
from openai import OpenAI

from git_gpt import __version__


@click.group()
@click.version_option(version=__version__, prog_name='git-gpt')
def cli():
    pass

@cli.command(help=f"Configure the CLI. Configuration will be saved to {os.path.expanduser('~/.config/git-gpt/config.json')}")
@click.option('--api-key', help='The API key to use with OpenAI.')
@click.option('--base', help='The alternative OpenAI host.')
@click.option('--model', help='The model to use for generating the commit message.')
@click.option('--lang', help='Target language for the generated message.')
@click.option('--issue-max-tokens', type=int, help='The maximum number of tokens to use for the issue prompt.')
def config(api_key, base, model, lang, issue_max_tokens):
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
<type>[optional scope]: <title>
- [detail 1]
- [detail 2]

"""


@cli.command()
@click.option('--lang', default=None, help='Target language for the generated message.')
@click.option('--model', default=None, help='The model to use for generating the commit message.')
@click.option('--run-dry', is_flag=True, help='Run the command to print the commit message without actually committing.')
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
    model = model or config.get('model', 'gpt-3.5-turbo')

    repo = git.Repo(os.getcwd())
    # add all changes to staged
    repo.git.add('--all')
    diffs = repo.git.diff('--staged')  # Get textual representation of staged diffs

    base_url = config.get('base', 'https://api.openai.com')

    client = OpenAI(api_key=config['api_key'], base_url=f"{base_url}/v1")

    # print loading animation
    click.echo(f"Generating commit message with {model} in {lang}...")

    prompt = commit_message_prompt

    # replace [insert_diff] with the actual diffs
    prompt = prompt.replace('[insert_diff]', diffs)
    # replace [insert_language] with the target language
    prompt = prompt.replace('[insert_language]', lang)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": f"You are a copilot programmer."},
            # {"role": "user", "content": f"Generate a commit message for the following diffs with a message under 50 characters and a list of description of features under 72 characters, written in {lang}.\nThe message should start with `feat:` or `fix`. Please summarize the Description in a list.\n\ndiffs:\n{diffs}"}
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
@click.option('--lang', default=None, help='Target language for the generated message.')
@click.option('--model', default=None, help='The model to use for generating the commit message.')
@click.option('--max-tokens', type=int, help='The maximum number of tokens to use for the issue prompt.')
@click.option('--commit-range', type=int, help='The maximum number of tokens to use for the issue prompt.')
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
    model = model or config.get('model', 'gpt-3.5-turbo')

    repo = git.Repo(os.getcwd())
    # read the diffs of the latest commit
    diffs = repo.git.diff(f'HEAD~{commit_range or 1}..HEAD')  # Get textual representation of staged diffs

    # if max tokens is not provided, use the default value
    max_tokens = max_tokens or config.get('issue_max_tokens', 1000)

    base_url = config.get('base', 'https://api.openai.com')
    client = OpenAI(api_key=config['api_key'], base_url=f"{base_url}/v1")

    # print loading animation
    click.echo(f"Generating issue using {model} in {lang}...")

    prompt = issue_prompt.replace('[insert_diff]', diffs).replace('[insert_language]', lang)

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
    commit_message = response['choices'][0]['message']['content'].strip()

    issue = response['choices'][0]['message']['content'].strip()
    
    click.echo(f"Issue created successfully:\n\n{issue}")


@cli.command()
@click.option('--lang', default=None, help='Target language for the generated message.')
@click.option('--model', default=None, help='The model to use for generating the quality check.')
@click.option('--max-tokens', type=int, help='The maximum number of tokens to use for the quality check.')
@click.option('--commit-range', type=int, help='The maximum number of tokens to use for the quality check.')
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
    model = model or config.get('model', 'gpt-3.5-turbo')

    repo = git.Repo(os.getcwd())
    diffs = repo.git.diff(f'HEAD~{commit_range or 1}..HEAD')

    max_tokens = max_tokens or config.get('quality_check_max_tokens', 1000)

    base_url = config.get('base', 'https://api.openai.com')
    client = OpenAI(api_key=config['api_key'], base_url=f"{base_url}/v1")

    click.echo(f"Performing quality check using {model} in {lang}...")


    prompt = (
        f"I have a `git diff` output from my recent code changes, and I need help with a quality check. "
        f"Could you assist me in reviewing the following aspects:\n\n"
        f"1. Code Consistency: Please analyze if the changes are consistent with the existing coding style and standards in the project.\n"
        f"2. Potential Bugs: Highlight any lines in the diff that might introduce bugs or logical errors.\n"
        f"3. Best Practices: Suggest any improvements or best practices that could be applied to the changes.\n"
        f"4. Documentation and Comments: Check if the new code is adequately commented and if any documentation needs to be updated.\n"
        f"5. Performance Implications: Evaluate if there are any changes that might adversely affect the performance of the code.\n\n"
        f"6. Security Check: Examine the code for potential security vulnerabilities, such as SQL injection, cross-site scripting, data leaks, or any other security risks.\n\n"
        f"Here's the `git diff` output:\n```diff\n{diffs}```\n\n"
        f"\nImportant: Please write a quality check report in `{lang}`."
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": f"You are a copilot programmer."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=max_tokens,
        stop=None
    )

    response = json.loads(response.model_dump_json())
    quality_check_result = response['choices'][0]['message']['content'].strip()

    click.echo(f"Quality check performed successfully:\n\n{quality_check_result}")


if __name__ == '__main__':
    cli()
