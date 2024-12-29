import click
from git_gpt import __version__
from git_gpt.config_command import config, set_default_model, delete_config_command, show_models_command
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

@cli.command()
@click.option('-a', '--alias', help='Model alias to set as default')
def set_default(alias):
    """Set the default model."""
    try:
        set_default_model(alias)
    except click.ClickException as e:
        click.echo(str(e), err=True)

@cli.command()
@click.option('-a', '--alias', required=False, help='Model alias to delete')
def delete_model(alias):
    """Delete a model configuration by alias."""
    delete_config_command(alias)

@cli.command()
def show_models():
    """Show all models with their provider and masked key."""
    show_models_command()

if __name__ == '__main__':
    cli()
