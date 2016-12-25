from datetime import timedelta, timezone, datetime as dt

import click
from jira.exceptions import JIRAError

import src.config as config
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
            date = date.replace(hour=0, minute=0, second=0, microsecond=0)

            io.print_date_line(date)

            started = date.astimezone(tz=timezone.utc)
            finished = started + timedelta(days=1) - timedelta(seconds=1)

            pub_issues, sk_issues = self.issues(started, finished)

            uncync_issues = self.unsync_sk_issues(pub_issues, sk_issues)

            if uncync_issues:
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
            pub_time = sum(pub_issue.spent_time for pub_issue in pub_issues)

            if sk_key is None:
                io.print_time_diff_line(pub_issues, None, time_diff=pub_time, status="warning")
                continue

            sk_issue = sk_issues[sk_key]

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
        keys = [key for key in sk_issues.keys()]
        if not click.confirm('Synchronize %s?' % str(keys), default=False):
            return

        for sk_key, sk_issue in sk_issues.items():
            pub_issues = pub_map[sk_key]

            for worklog in sk_issue.worklogs:
                self._sk_jira.remove_worklog(sk_issue, worklog)

            worklogs = [worklog for issue in pub_issues for worklog in issue.worklogs]

            for worklog in worklogs:
                started = config.Jira.jira_time_to_dt(worklog.started)

                self._sk_jira.add_worklog(sk_issue, timeSpentSeconds=worklog.timeSpentSeconds, started=started,
                                          comment=worklog.comment)

    def sk_issues(self, sk_keys, started, finished):
        """
        Get SK issues by keys and adding worklog by date

        :param sk_keys: list
        :param started: dt
        :param finished: dt

        :return:
        """
        result = {}

        for sk_key in sk_keys:
            try:
                sk_issue = self._sk_jira.issue(sk_key)
                sk_issue.__class__ = config.Issue

                sk_issue.worklogs = self._sk_jira.worklogs_by_dates(sk_issue, started, finished)

                result[sk_key] = sk_issue
            except JIRAError:
                result[None] = None

        return result

    def issues(self, started, finished):
        """
        Return PUB and SK issues by worklog between started and finished

        :rtype: dict
        """
        pub_map, sk_map = {}, {}

        sk_issues = self._sk_jira.issues_by_worklog_date(started)
        pub_issues = self._pub_jira.issues_by_worklog_date(started)

        external_ids = [issue.external_url for issue in pub_issues]

        additional_external_id = [sk_issue.permalink() for sk_issue in sk_issues if
                                  sk_issue.permalink() not in external_ids]

        pub_issues += self.pub_issue_by_sk_urls(additional_external_id)

        for issue in pub_issues:
            issue.__class__ = config.Issue
            issue.worklogs = self._pub_jira.worklogs_by_dates(issue, started, finished)

            sk_key = issue.external_key

            pub_map[sk_key] = pub_map.get(sk_key, []) + [issue]

        sk_keys = [sk_issue.key for sk_issue in sk_issues]

        addition_sk_keys = [key for key in pub_map.keys() if key is not None and key not in sk_keys]

        sk_issues += [self._sk_jira.issue(key) for key in addition_sk_keys]

        for issue in sk_issues:
            issue.__class__ = config.Issue
            issue.worklogs = self._sk_jira.worklogs_by_dates(issue, started, finished)

            sk_map[issue.key] = issue

        return pub_map, sk_map

    def pub_issue_by_sk_urls(self, urls):
        pub_issues = []

        for url in urls:
            pub_issues += self._pub_jira.search_issues("'External issue ID' ~ '%s'" % url)

        return pub_issues
