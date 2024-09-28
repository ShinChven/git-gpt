import json
import os
import click
import git
from .request_module import RequestModule

system_instruction = "You are going to work as a text generator, **you don't talk at all**, you will print your response in plain text without code block."

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

@click.command()
@click.option('--lang', '-l', default=None, help='Target language for the generated message.')
@click.option('--model', '-m', default=None, help='The model to use for generating the commit message.')
@click.option('--max-tokens', '-t', type=int, help='The maximum number of tokens to use for the issue prompt.')
@click.option('--commit-range', '-r', type=int, help='The number of commits to include in the diff.')
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
    model = model or config.get('model', 'gpt-4o-mini')

    repo = git.Repo(os.getcwd())
    # read the diffs of the latest commit
    diff = repo.git.diff(f'HEAD~{commit_range or 1}..HEAD')  # Get textual representation of staged diffs

    # if max tokens is not provided, use the default value
    max_tokens = max_tokens or config.get('issue_max_tokens', 2000)

    api_type = config.get('api_type', 'openai')
    if api_type == 'openai':
        base_url = config.get('base', 'https://api.openai.com')
    elif api_type == 'ollama':
        base_url = config.get('ollama_base', 'http://localhost:11434')
    else:
        raise ValueError(f"Unsupported API type: {api_type}")

    request_module = RequestModule(api_type=api_type, api_key=config['api_key'], api_base=base_url)

    # print loading animation
    click.echo(f"Generating issue using {model} in {lang}...")

    prompt = issue_prompt.replace('[insert_diff]', diff).replace('[insert_language]', lang)

    messages = [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": prompt}
    ]

    response = request_module.send_request(messages=messages, model=model, temperature=0.7)

    issue = response['choices'][0]['message']['content'].strip()
    
    click.echo(f"Issue created successfully:\n\n{issue}")