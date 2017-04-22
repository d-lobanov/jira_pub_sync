from datetime import datetime as dt

import jira


def jira_time_to_dt(jira_time):
    """
    :type jira_time: str

    :rtype: dt
    """
    return dt.strptime(jira_time, '%Y-%m-%dT%H:%M:%S.%f%z')


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]


def unique(l):
    return list(set(filter(None, l)))


class JiraHelper(object):
    MAX_RESULT = 100000

    def __init__(self, jira):
        """
        :type jira: jira.JIRA
        """
        self.connection = jira
        self._current_user = jira.current_user()

    def merge_issues(self, first_issues, second_issues):
        return {issue.id: issue for issue in first_issues + second_issues}.values()

    def issues_by_worklog_date_range(self, date_start, date_finish):
        """
        :type date_start: dt
        :type date_finish: dt

        :rtype: ReslutList
        """

        return self.connection.search_issues(
            "worklogDate >= '%s' and worklogDate <= '%s' and worklogAuthor=currentUser()" %
            (date_start.strftime("%Y/%m/%d"), date_finish.strftime("%Y/%m/%d")))

    def remove_worklog(self, issue, worklog):
        """
        :type issue: jira.issue
        :type worklog: jira.Worklog

        :rtype: str
        """
        url = self.connection._get_url(worklog._resource.format(issue.id, worklog.id))

        self.connection._session.delete(url)

    def remove_worklogs(self, issue, worklogs):
        [self.remove_worklog(issue, worklog) for worklog in worklogs]

    def add_worklog(self, issue, worklog):
        self.connection.add_worklog(issue, timeSpentSeconds=worklog.total_time,
                                    started=jira_time_to_dt(worklog.started),
                                    comment=worklog.comment)

    def get_worklogs_by_date(self, issue, date_start, date_finish):
        """
        :type issues: dict
        :type date_start: str
        :type date_finish: str

        :rtype: dict
        """
        try:
            self.connection.async_do()
            return [worklog for worklog in self.connection.worklogs(issue) if
                    worklog.author.name == self._current_user and
                    date_start < jira_time_to_dt(worklog.started) < date_finish]

        except:
            return None

    def issues(self, keys):
        """
        Get all issues by keys.

        :param keys:
        :return:
        """
        issues = []

        for chunk in chunks(unique(keys), 100):
            jql = "key in ('" + "','".join(chunk) + "')"

            issues += self.connection.search_issues(jql, maxResults=self.MAX_RESULT, validate_query=False)

        return issues


class PubHelper(JiraHelper):
    def get_issues_by_sk_links(self, links):
        """
        Finds issues by sk links.

        :type links: list

        :return:
        """
        pub_issues = []

        for chunk in chunks(unique(links), 40):
            jql = "'External issue ID' ~ '" + "' OR 'External issue ID' ~ '".join(chunk) + "'"

            pub_issues += self.connection.search_issues(jql, maxResults=self.MAX_RESULT, validate_query=False)

        return pub_issues
