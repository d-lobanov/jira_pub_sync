from src import config
from src.io import IO
from src.time_synchronizer import TimeSynchronizer
import click

try:
    import ConfigParser as configparser
except ImportError:
    import configparser


def main():
    try:
        sk_jira = config.JiraFactory.create_sk()
        pub_jira = config.JiraFactory.create_pub()
    except (configparser.NoSectionError, configparser.NoOptionError):
        click.echo('Please, edit config file %s' % click.format_filename(config.AppConfig.get_file_path()))
        return

    started = IO.input_days_ago()

    TimeSynchronizer(pub_jira, sk_jira).do_from(started)


main()
