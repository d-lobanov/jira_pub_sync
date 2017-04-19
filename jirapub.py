import click

from src import AppConfig
from src import BaseFactory
from src import IO
from src import IssueSync
from src import JiraFactory
from src import TimeSynchronizer
from src import day_ago_to_datetime


def input_createntials(config):
    """
    Read user input and check if credentials are valid.
    """
    while True:
        try:
            config = IO.input_jira_credentials(config.url, config.username, config.password)

            BaseFactory.create_jira(config)
        except Exception:
            IO.error('Credentials not valid')
            click.confirm('Try again?', default=True, abort=True)

        return config


@click.group()
def cli():
    pass


@cli.command()
def config():
    """
    Change credentials of JIRAs.
    """
    click.echo('Jira-pub')

    pub_config = input_createntials(AppConfig.read_pub_config())

    if pub_config:
        IO.success('PUB credentials are valid')
        AppConfig.write_pub_config(pub_config)

    click.echo('\nSK Jira')

    sk_config = input_createntials(AppConfig.read_sk_config())
    if sk_config:
        IO.success('SK credentials are valid')
        AppConfig.write_sk_config(sk_config)


@cli.command()
@click.argument('issue_key', required=False, type=str)
def issue(issue_key):
    """Migrates JIRA ticket from SK to PUB.

    Uses SK issue key as argument for migration.
    Migrates type, description, status, attachments of task.
    Also, adds label `auto_migration` for easy finding.

    You can change title, estimate etc in the process.
    """
    sk, pub = JiraFactory.create()

    if not issue_key:
        issue_key = click.prompt('SK issue key', type=str)

    IssueSync(sk, pub).migrate(issue_key.strip())


@cli.command()
@click.argument('days_ago', required=False, type=int)
def issues(days_ago):
    """Migrate non-synchronized tickets from SK to PUB since from DAYS_AGO till NOW
    \b

    Finds non-synchronized tickets by using worklogs and assigned tasks in SK for current user.
    Provides git-like interface to choose which tickets have to be migrated.
    After that, it uses `issue` command for each of a task.

    Can synchronize maximum 1000 days.
    """
    sk, pub = JiraFactory.create()

    if days_ago and 1 < days_ago < 1000:
        started = day_ago_to_datetime(days_ago)
    else:
        started = IO.input_days_ago(default=14, limit=1000)

    IssueSync(sk, pub).migrate_issues(started)


@cli.command()
@click.argument('days_ago', required=False, type=int)
def time(days_ago):
    """Time synchronization between JIRAs from DAYS_AGO till NOW

    Finds existing worklogs in SK and PUB JIRA.
    Compares them by using `External ID`.
    Migrates all worklogs from PUB to SK if time differences exists.
    Uses PUB as a primary source.
    Migrates comments for worklogs as well.

    Can synchronize maximum 100 days.
    """
    sk, pub = JiraFactory.create()

    if days_ago and 1 < days_ago < 100:
        started = day_ago_to_datetime(days_ago)
    else:
        started = IO.input_days_ago(default=5, limit=100)

    TimeSynchronizer(sk, pub).do(started)

if __name__ == '__main__':
    cli()
