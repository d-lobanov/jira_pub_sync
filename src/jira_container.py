import re

import jira

from src.jira_helper import jira_time_to_dt


def parse_key_from_issue_url(url):
    """
    Get key of issue by Url.
    """
    if url is None:
        return None

    r = re.match('^(https?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})\/(browse)\/(?P<key>\w+-\d+)$', url)

    return r.group('key') if r else None


def date_to_timestamp_range(date):
    """
    Get first and last second of day.
    """
    start = date.replace(hour=0, minute=0, second=0)
    finsh = date.replace(hour=23, minute=59, second=59)

    return start.timestamp(), finsh.timestamp()


class Decorator(object):
    def __getattr__(self, key):
        if not hasattr(self.data, key):
            raise AttributeError

        return getattr(self.data, key)


class Issue(Decorator):
    """
    Decorator for issue. Extends default functionality.
    """

    def __init__(self, issue, worklogs=None):
        """
        :type issue jira.Issue
        """
        self.data = issue
        self.worklogs = WorklogsCollection(worklogs)

    @property
    def link(self):
        return self.data.permalink()

    @property
    def summary(self):
        return self.data.fields.summary

    def has_worklog_on_date(self, date):
        return self.worklogs.has_worklog_on_date(date)


class PubIssue(Issue):
    """
    Decorator for pub issue.
    """

    def __init__(self, issue, worklogs=None):
        super().__init__(issue, worklogs)

        self.sk_key = parse_key_from_issue_url(self.sk_url)

    @property
    def sk_url(self):
        return getattr(self.data.fields, 'customfield_10105')


class Worklog(Decorator):
    """
    Decorator for worklog. Extends default functionality.
    """

    def __init__(self, worklog):
        self.data = worklog
        self.time_started = jira_time_to_dt(self.data.started).timestamp()

    @property
    def total_time(self):
        return int(self.data.timeSpentSeconds)


class IssuesCollection(object):
    """
    Collections of issue decorators.
    """

    def __init__(self, issues):
        self._issues = []

        [self._add(issue) for issue in issues]

    def __iter__(self):
        return iter(self._issues)

    @property
    def keys(self):
        return [issue.key for issue in self._issues]

    @property
    def links(self):
        return [issue.link for issue in self._issues]

    @property
    def items(self):
        return self._issues

    @property
    def _item_class(self):
        return Issue

    def first(self):
        return next(iter(self._issues), None)

    def total_worklog_time(self):
        return [issue.t for issue in self._issues]

    def merge(self, issues):
        [self.add(issue) for issue in issues]

    def add(self, issue):
        if not self.contains(issue):
            self._add(issue)

    def contains(self, issue):
        key = issue.key

        return any(key == issue.key for issue in self._issues)

    def filter_by_worklog_date(self, date):
        return self.__class__([issue for issue in self._issues if issue.has_worklog_on_date(date)])

    def total_worklogs_time(self, date):
        return sum([issue.worklogs.filter_by_date(date).total_time for issue in self._issues])

    def get(self, key):
        if key is None:
            return None

        return next((issue for issue in self._issues if issue.key == key), None)

    def _add(self, issue):
        issue = issue if isinstance(issue, self._item_class) else self._item_class(issue)

        self._issues.append(issue)


class PubIssuesCollection(IssuesCollection):
    @property
    def sk_keys(self):
        return [issue.sk_key for issue in self._issues]

    @property
    def _item_class(self):
        return PubIssue

    def filter_by_sk_key(self, sk_key):
        return self.__class__([issue for issue in self._issues if issue.sk_key == sk_key])


class WorklogsCollection(object):
    """
    Collections of worklogs decorators.
    """

    def __init__(self, worklogs=None):
        self._worklogs = []

        [self._add(worklog) for worklog in worklogs or []]

    def __iter__(self):
        return iter(self._worklogs)

    @property
    def total_time(self):
        return sum([worklog.total_time for worklog in self._worklogs])

    def filter_by_date(self, date):
        start, finish = date_to_timestamp_range(date)

        return WorklogsCollection([worklog for worklog in self._worklogs if start < worklog.time_started < finish])

    def has_worklog_on_date(self, date):
        start, finish = date_to_timestamp_range(date)

        return any(start < worklog.time_started < finish for worklog in self._worklogs)

    def contains(self, worklog):
        id = worklog.id

        return any(id == worklog.id for worklog in self._worklogs)

    def merge(self, worklogs):
        [self.add(worklog) for worklog in worklogs]

    def add(self, worklog):
        if not self.contains(worklog):
            self._add(worklog)

    def _add(self, worklog):
        worklog = worklog if isinstance(worklog, Worklog) else Worklog(worklog)

        self._worklogs.append(worklog)
