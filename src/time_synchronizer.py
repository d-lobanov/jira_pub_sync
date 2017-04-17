from datetime import timedelta, datetime as dt

import click

from src.jira_container import IssuesCollection, PubIssuesCollection, WorklogsCollection
from src.jira_helper import JiraHelper, PubHelper
from src.io import IO as io


def date_range(start, end):
    days = int((end - start).days) + 1

    for n in range(days):
        yield start + timedelta(n)


class TimeSynchronizer(object):
    def __init__(self, pub_jira, sk_jira):
        """
        :type _pub_helper: JiraHelper
        :param pub_jira:

        :type _sk_helper: JiraHelper
        :param sk_jira:

        """
        self._pub_jira = pub_jira
        self._sk_jira = sk_jira

        self._pub_helper = PubHelper(pub_jira)
        self._sk_helper = JiraHelper(sk_jira)

    def do(self, date_start):
        """
        Find and sync differences between JIRAs

        :type date_start: dt
        :param date_start:

        """
        date_start = date_start.replace(hour=0, minute=0, second=0, microsecond=0)
        date_finish = dt.today().replace(tzinfo=date_start.tzinfo, hour=23, minute=59, second=59)

        sk, pub = self._get_issues_collections(date_start, date_finish)

        for date in date_range(date_start, date_finish):
            io.echo_date(date)

            sk_keys = sk.filter_by_worklog_date(date).keys
            sk_keys += pub.filter_by_worklog_date(date).sk_keys

            sk_keys = list(set(sk_keys))

            worklogs_diff = []

            for sk_key in sk_keys:
                sk_issue = sk.get(sk_key)
                sk_worklogs = sk_issue.worklogs.filter_by_date(date) if sk_issue else WorklogsCollection()

                pub_collection = pub.filter_by_sk_key(sk_key).filter_by_worklog_date(date)

                time_diff = pub_collection.total_worklogs_time(date) - sk_worklogs.total_time

                if time_diff != 0 and sk_issue:
                    worklogs_diff.append((sk_issue, pub_collection, date))

                self._print_line(time_diff, sk_issue, pub_collection)

            if worklogs_diff and self._confirm(worklogs_diff):
                self._sync_time(worklogs_diff)

    def _confirm(self, worklogs_diff):
        return click.confirm('Do you want to synchronize tasks %s?' % [item[0].key for item in worklogs_diff])

    def _print_line(self, time_diff, sk_issue=None, pub_collection=None):
        """
        Print time differences information.
        """
        pub_link = io.highlight_key(issue=pub_collection.first()) if pub_collection else None
        sk_link = io.highlight_key(issue=sk_issue) if sk_issue else None

        summary = sk_issue.summary if sk_issue else pub_collection.first().summary

        click.echo(
            '%s => %s [ %s ] %s' % (pub_link, sk_link, io.highlight_time(time_diff), io.truncate_summary(summary)))

        for issue in pub_collection.items[1:]:
            click.echo('%s' % io.highlight_key(issue=issue))

    def _sync_time(self, items):
        """
        :type issue: IssuesCollection
        """
        for issue, pub_collection, date in items:
            self._sk_helper.remove_worklogs(issue.data, issue.worklogs.filter_by_date(date))

            for pub_issue in pub_collection:
                [self._sk_helper.add_worklog(issue.data, worklog) for worklog in
                 pub_issue.worklogs.filter_by_date(date)]

            click.echo('Synchronized %s' % io.highlight_key(issue=issue))

    def _get_issues_collections(self, date_start, date_finish):
        """
        Returns two collection of Issues for both of JIRAs.
        """
        sk_issues = self._sk_helper.issues_by_worklog_date_range(date_start, date_finish)
        pub_issues = self._pub_helper.issues_by_worklog_date_range(date_start, date_finish)

        sk_collection = IssuesCollection(sk_issues)
        pub_collection = PubIssuesCollection(pub_issues)

        sk_issues = self._sk_helper.issues(pub_collection.sk_keys)
        pub_issues = self._pub_helper.get_issues_by_sk_links(sk_collection.links)

        sk_collection.merge(sk_issues)
        pub_collection.merge(pub_issues)

        sk_collection = self._add_sk_worklogs(sk_collection, date_start, date_finish)
        pub_collection = self._add_pub_worklogs(pub_collection, date_start, date_finish)

        return sk_collection, pub_collection

    def _add_sk_worklogs(self, collection, date_start, date_finish):
        """
        Adds worklogs into SK collection and returns updated collection.
        """
        for issue in collection:
            worklogs = self._sk_helper.get_worklogs_by_date(issue.data, date_start, date_finish)

            if worklogs:
                issue.worklogs.merge(worklogs)

        return collection

    def _add_pub_worklogs(self, collection, date_start, date_finish):
        """
        Adds worklogs into PUB collection and returns updated collection.
        """
        for issue in collection:
            worklogs = self._pub_helper.get_worklogs_by_date(issue.data, date_start, date_finish)

            if worklogs:
                issue.worklogs.merge(worklogs)

        return collection
