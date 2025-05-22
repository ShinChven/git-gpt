import git
import os
import click

def get_git_diff(commit_range: int | None = None) -> str:
    """
    Retrieves the git diff for the specified commit range.

    Args:
        commit_range: The number of commits to include in the diff. Defaults to 1.

    Returns:
        The git diff as a string.
    """
    repo = git.Repo(os.getcwd())
    effective_commit_range = commit_range or 1
    diff_command = f'git diff HEAD~{effective_commit_range}..HEAD'
    click.echo(f"Running git command: {diff_command}")
    diff = repo.git.diff(f'HEAD~{effective_commit_range}..HEAD')
    return diff
