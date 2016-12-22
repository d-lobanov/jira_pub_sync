from datetime import timedelta, timezone, datetime as dt

from jira.exceptions import JIRAError

import src.config as config
import click
from src.io import IO as io


def date_range(start, end):
    days = int((end - start).days) + 1

    for n in range(days):
        yield start + timedelta(n)


class TimeSynchronizer(object):
    def __init__(self, pub_jira, sk_jira):
        """
        :type pub_jira: config.Jira
        :param pub_jira:

        :type sk_jira: config.Jira
        :param sk_jira:

        """
        self._pub_jira = pub_jira
        self._sk_jira = sk_jira

    def do_from(self, started):
        """
        Find and sync differences between JIRAs

        :type started: dt
        :param started:

        """
        today = dt.today().replace(tzinfo=started.tzinfo)

        for date in date_range(started, today):
            date = date.astimezone(tz=timezone.utc)

            io.print_date_line(date)

            pub_issues = self.pub_issues(date)
            sk_issues = self.sk_issues(pub_issues.keys(), date)

            uncync_issues = self.unsync_sk_issues(pub_issues, sk_issues)

            self.sync(uncync_issues, pub_issues)

    def unsync_sk_issues(self, pub_map, sk_issues):
        """
        Get all SK issues with different time
        Print each step

        :param pub_map:
        :param sk_issues:
        :return:
        """
        unsync_sk_issues = {}
        for sk_key, pub_issues in pub_map.items():
            sk_issue = sk_issues[sk_key]

            pub_time = sum(pub_issue.spent_time for pub_issue in pub_issues)

            if sk_issue is None:
                io.print_time_diff_line(pub_issues, sk_issue, time_diff=pub_time, status="warning")
                continue

            time_diff = pub_time - sk_issue.spent_time

            io.print_time_diff_line(pub_issues, sk_issue, time_diff)

            if time_diff != 0:
                unsync_sk_issues[sk_key] = sk_issue

        return unsync_sk_issues

    def sync(self, sk_issues, pub_map):
        """
        Remove all worklog from SK issue and move PUB worklogs to SK
        Ask user before doing

        :param sk_issues:
        :param pub_map:
        :return:
        """
        for sk_key, sk_issue in sk_issues.items():
            pub_issues = pub_map[sk_key]

            keys = [pub_issue.key for pub_issue in pub_issues]
            if not click.confirm('Synchronize %s?' % keys, default=False):
                continue

            for worklog in sk_issue.worklogs:
                self._sk_jira.remove_worklog(sk_issue, worklog)

            worklogs = [worklog for issue in pub_issues for worklog in issue.worklogs]

            for worklog in worklogs:
                started = config.Jira.jira_time_to_dt(worklog.started)

                self._sk_jira.add_worklog(sk_issue, timeSpentSeconds=worklog.timeSpentSeconds, started=started,
                                          comment=worklog.comment)

    def sk_issues(self, sk_keys, worklog_date):
        """
        Get SK issues by keys and adding worklog by date

        :param sk_keys: list
        :param worklog_date: dt

        :return:
        """
        result = {}

        for sk_key in sk_keys:
            try:
                sk_issue = self._sk_jira.issue(sk_key)
                sk_issue.__class__ = config.Issue

                sk_issue.worklogs = self._sk_jira.worklogs_by_date(sk_issue, worklog_date)

                result[sk_key] = sk_issue
            except JIRAError:
                result[None] = None

        return result

    def pub_issues(self, started):
        """
        Return pub issues by date

        :rtype: dict
        """
        result = {}
        issues = self._pub_jira.issues_by_worklog_date(started)

        for issue in issues:
            issue.worklogs = self._pub_jira.worklogs_by_date(issue, started)

            sk_key = issue.external_key

            result[sk_key] = result.get(sk_key, []) + [issue]

        return result
