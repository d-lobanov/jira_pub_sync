from src.io import IO
from src.time_synchronizer import TimeSynchronizer
from src.decorators import except_abort
from src.jira_factory import JiraFactory

try:
    import ConfigParser as configparser
except ImportError:
    import configparser


@except_abort
def main():
    sk, pub = JiraFactory.createOrAbort()

    started = IO.input_days_ago(5)

    TimeSynchronizer(sk, pub).do(started)


main()
