import click
from git_gpt import __version__
from git_gpt.config_command import config
from git_gpt.commit_command import commit
from git_gpt.issue_command import issue
from git_gpt.quality_command import quality
from git_gpt.changelog_command import changelog
from git_gpt.ask_command import ask

default_model = 'gpt-4o-mini'

@click.group()
@click.version_option(version=__version__, prog_name='git-gpt')
def cli():
    pass

cli.add_command(config)
cli.add_command(commit)
cli.add_command(issue)
cli.add_command(quality)
cli.add_command(changelog)
cli.add_command(ask)

if __name__ == '__main__':
    cli()
