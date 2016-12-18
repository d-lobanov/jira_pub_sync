from datetime import timedelta, datetime as dt
import src.config as config
import click
from src.io import IO as io


def date_range(start, end):
    days = int((end.replace(tzinfo=None) - start.replace(tzinfo=None)).days)

    for n in range(days + 1):
        yield days - n, start + timedelta(n)


class Synchronizer:
    def __init__(self, pub_jira, sk_jira):
        self._pub_jira = pub_jira
        self._sk_jira = sk_jira

    def sync(self, started):
        for days_ago, date in date_range(started, dt.today()):
            pub_issues = self._pub_jira.issues_by_worklog_date(days_ago)

            if pub_issues:
                io.print_date_line(date)
                self.sync_worklogs(date, pub_issues)

    def unsync_sk_issues(self, date, pub_issues):
        issues = []
        for pub_issue in pub_issues:
            sk_issue = self.sk_issue(pub_issue)
            if not sk_issue:
                continue

            time_diff = self.get_timespend_diff(date, pub_issue, sk_issue)
            io.print_time_diff_line(pub_issue, sk_issue.permalink(), time_diff)

            if time_diff > 0:
                sk_issue.time_diff = time_diff
                issues.append(sk_issue)

        return issues

    def sync_worklogs(self, date, pub_issues):
        sk_issues = self.unsync_sk_issues(date, pub_issues)
        if not sk_issues:
            return

        keys = [issue.key for issue in sk_issues]
        if not click.confirm('Synchronize %s?' % keys, default=False):
            return

        for issue in sk_issues:
            self._sk_jira.add_worklog(issue, started=date, timeSpentSeconds=issue.time_diff)
            # self._sk_jira.add_worklog(issue, started=date, timeSpentSeconds=15 * 60)

    def sk_issue(self, pub_issue):
        """Return sk issue by pub issue

        :rtype: config.Issue
        """
        sk_key = pub_issue.external_key()
        if sk_key is None:
            io.print_line(pub_issue, None, 'Missing external ID', status='warning')
            return None

        sk_issue = self._sk_jira.issue(sk_key)
        if sk_issue is None:
            io.print_line(pub_issue, pub_issue.external_url(), 'Couldn\'t find task', status='warning')
            return None

        return sk_issue

    def get_timespend_diff(self, date, pub_issue, sk_issue):
        """Get time difference in seconds between two JIRAs

        :rtype: int
        """
        pub_time = self._pub_jira.timespend(pub_issue, date)
        sk_time = self._sk_jira.timespend(sk_issue, date)

        return pub_time - sk_time
