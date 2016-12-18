from src import config
from src.io import IO
from src.synchronizer import Synchronizer as Sync
import click
import pytz

try:
    import ConfigParser as configparser
except ImportError:
    import configparser


def main():
    try:
        sk_jira = config.JiraFactory.get_sk()
        pub_jira = config.JiraFactory.get_pub()
    except (configparser.NoSectionError, configparser.NoOptionError):
        click.echo('Please, edit config file %s' % click.format_filename(config.AppConfig.get_file_path()))
        return

    started = IO.input_days_ago()
    started = pytz.timezone(pub_jira.timezone()).localize(started)

    Sync(pub_jira, sk_jira).sync(started)

main()
