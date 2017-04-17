import click

import src.jira
from src import config
from src.decorators import except_abort
from src.issue_synchronizer import IssueSync

try:
    import ConfigParser as configparser
except ImportError:
    import configparser


@except_abort
def main():
    try:
        sk_jira = src.jira.JiraFactory.create_sk()
        pub_jira = src.jira.JiraFactory.create_pub()
    except (configparser.NoSectionError, configparser.NoOptionError):
        click.echo('Please, edit config file %s' % click.format_filename(config.AppConfig.get_file_path()))
        return

    sk_key = click.prompt('SK issue number', type=str)

    IssueSync(pub_jira, sk_jira).do(sk_key.strip())


main()
