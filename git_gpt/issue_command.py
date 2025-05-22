import click
import git
from .config_command import get_config
import os
from .ai_client import AIClient
from .git_diff import get_git_diff

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
    config = get_config()

    lang = lang or config.get('lang', 'English')
    model = model or config.get('default_model')

    if not model:
        raise ValueError("No default model specified in configuration. Please run git-gpt set-default to set default model or run git-gpt config to add model configuration.")

    diff = get_git_diff(commit_range)

    max_tokens = max_tokens or config.get('issue_max_tokens') or None

    ai_client = AIClient(config)

    try:
        click.echo(f"Generating issue using {model} in {lang}...")

        prompt = issue_prompt.replace('[insert_diff]', diff).replace('[insert_language]', lang)

        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt}
        ]

        response = ai_client.request(messages=messages, model_alias=model, max_tokens=max_tokens)
        issue_content = response
        click.echo(f"Issue generated successfully:\n\n{issue_content}")
    except ValueError as e:
        click.echo(f"Error: {str(e)}")
        click.echo("Please make sure you have set the API key using `git-gpt config --api-key <API_KEY>`")
    except Exception as e:
        click.echo(f"Error generating issue: {str(e)}")
        click.echo("Please check the ai_client.py file for more details on the error.")
