from src.io import IO
from src.config import AppConfig, JiraFactory
import click

try:
    import ConfigParser as configparser
except ImportError:
    import configparser


def jira_credential(url, section):
    credentials = (url, None, None)

    try:
        pub_old = AppConfig.read_jira_config(section)
        credentials = (pub_old.url, pub_old.username, pub_old.password)
    except (configparser.NoSectionError, configparser.NoOptionError):
        pass

    while True:
        try:
            config = IO.input_jira_credentials(*credentials)
            JiraFactory.create(config)
        except Exception:
            click.secho(click.style('Credentials are not valid', fg='red'))
            if click.confirm('Try again?', default=True):
                credentials = (config.url, config.username, config.password)
                continue

            return

        click.secho(click.style('Credentials are valid', fg='green'))
        AppConfig.write_jira_config(section, config)
        return


def clean_hidden_issues():
    if click.confirm('Are you sure?'):
        AppConfig.write_hidden_keys([], True)


def main():
    click.echo('Jira-pub')
    jira_credential('https://jira-pub.itransition.com', AppConfig.PUB_SECTION)

    click.echo('\nSK Jira')
    jira_credential('https://sheknows.jira.com', AppConfig.SK_SECTION)


main()
