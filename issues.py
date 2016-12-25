import click

from src import config
from src.decorators import except_abort
from src.io import IO as io
from src.issue_synchronizer import IssueSync

try:
    import ConfigParser as configparser
except ImportError:
    import configparser


@except_abort
def main():
    try:
        sk_jira = config.JiraFactory.create_sk()
        pub_jira = config.JiraFactory.create_pub()
    except (configparser.NoSectionError, configparser.NoOptionError):
        click.echo('Please, edit config file %s' % click.format_filename(config.AppConfig.get_file_path()))
        return

    started = io.input_days_ago(default=14)

    IssueSync(pub_jira, sk_jira).do_many(started)


main()
