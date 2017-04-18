import click

from src import AppConfig
from src import BaseFactory
from src import IO
from src import IssueSync
from src import JiraFactory
from src import TimeSynchronizer


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
    """
    Migrate JIRA ticket from SK to PUB.
    """
    sk, pub = JiraFactory.create()

    if not issue_key:
        issue_key = click.prompt('SK issue key', type=str)

    IssueSync(sk, pub).migrate(issue_key.strip())


@cli.command()
def issues():
    """
    Migrate non-synchronized tickets from SK to PUB.
    """
    sk, pub = JiraFactory.create()

    started = IO.input_days_ago(default=14, limit=1000)

    IssueSync(sk, pub).migrate_issues(started)


@cli.command()
def time():
    """
    Time synchronization between JIRAs.
    """
    sk, pub = JiraFactory.create()

    started = IO.input_days_ago(default=5, limit=100)

    TimeSynchronizer(sk, pub).do(started)


if __name__ == '__main__':
    cli()
