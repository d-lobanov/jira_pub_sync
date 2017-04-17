from src.io import IO
from src.config import AppConfig, JiraConfig
from src.jira_factory import PubFactory, SkFactory, BaseFactory
import click

try:
    import ConfigParser as configparser
except ImportError:
    import configparser


def input_createntials(config):
    while True:
        try:
            config = IO.input_jira_credentials(config.url, config.username, config.password)

            BaseFactory.create_jira(config)
        except Exception:
            click.secho(click.style('Credentials are not valid', fg='red'))
            if click.confirm('Try again?', default=True):
                continue

            return None

        click.secho(click.style('Credentials are valid', fg='green'))

        return config


def clean_hidden_issues():
    if click.confirm('Are you sure?'):
        AppConfig.write_hidden_keys([], True)


def main():
    click.echo('Jira-pub')

    pub_config = input_createntials(AppConfig.read_pub_config())
    if pub_config:
        AppConfig.write_pub_config(pub_config)

    click.echo('\nSK Jira')

    sk_config = input_createntials(AppConfig.read_sk_config())
    if sk_config:
        AppConfig.write_sk_config(sk_config)


main()
