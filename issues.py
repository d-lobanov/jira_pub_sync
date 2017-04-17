from src.decorators import except_abort
from src.io import IO as io
from src.issue_synchronizer import IssueSync
from src.jira_factory import JiraFactory

try:
    import ConfigParser as configparser
except ImportError:
    import configparser


@except_abort
def main():
    sk, pub = JiraFactory.createOrAbort()

    started = io.input_days_ago(default=14)

    IssueSync(sk, pub).do_many(started)


main()
