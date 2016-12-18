from src import config
from src.io import IO
from src.synchronizer import Synchronizer as Sync
import click

try:
    import ConfigParser as configparser
except ImportError:
    import configparser


def main():
    try:
        sk_jira = config.JiraFactory.get_sk()
        pub_jira = config.JiraFactory.get_pub()
    except (configparser.NoSectionError, configparser.NoOptionError):
        click.echo('Please, edit config file')
        return

    started = IO.input_days_ago()

    sync = Sync(pub_jira, sk_jira)
    sync.sync(started)

main()
