import click
from src.decorators import except_abort
from src.issue_synchronizer import IssueSync
from src.jira_factory import JiraFactory

try:
    import ConfigParser as configparser
except ImportError:
    import configparser


@except_abort
def main():
    sk, pub = JiraFactory.createOrAbort()

    sk_key = click.prompt('SK issue number', type=str)

    IssueSync(sk, pub).do(sk_key.strip())


main()
