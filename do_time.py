from jira import JIRAError
from src.io import IO
from src.time_synchronizer import TimeSynchronizer
import click
from src.decorators import except_abort
from src.jira_factory import SkFactory, PubFactory

try:
    import ConfigParser as configparser
except ImportError:
    import configparser


@except_abort
def main():
    try:
        sk_jira = SkFactory.create()
        pub_jira = PubFactory.create()
    except (configparser.NoSectionError, configparser.NoOptionError):
        click.echo('Can\'t find valid configs. Please, check configs')
        return
    except JIRAError:
        click.echo('Can\'t connect to JIRA. Please, check configs')
        return

    started = IO.input_days_ago(5)

    TimeSynchronizer(pub_jira, sk_jira).do(started)


main()
