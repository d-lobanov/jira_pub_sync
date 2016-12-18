import jira
import click
import os
import re
from datetime import datetime as dt

try:
    import ConfigParser as configparser
except ImportError:
    import configparser

APP_NAME = 'JiraPubSync'


class AppConfig:
    SK_SECTION = 'SK_JIRA'
    PUB_SECTION = 'PUB_JIRA'

    @classmethod
    def get_file_path(cls):
        return os.path.join(cls.get_dir_path(), 'config.ini')

    @classmethod
    def get_dir_path(cls):
        return click.get_app_dir(APP_NAME, False, False)

    @classmethod
    def read(cls):
        config = configparser.RawConfigParser()
        config.read([cls.get_file_path()])

        return config

    @classmethod
    def write(cls, config):
        dir_path = cls.get_dir_path()
        if not os.path.isdir(dir_path):
            os.makedirs(dir_path, exist_ok=True)

        with open(cls.get_file_path(), 'w') as configfile:
            config.write(configfile)

    @classmethod
    def write_jira_config(cls, section, jira_config):
        config = cls.read()
        if not config.has_section(section):
            config.add_section(section)

        config.set(section, 'url', jira_config.url)
        config.set(section, 'username', jira_config.username)
        config.set(section, 'password', jira_config.password)

        cls.write(config)

    @classmethod
    def get_jira_config(cls, section):
        config = cls.read()

        url = config.get(section, 'url')
        username = config.get(section, 'username')
        password = config.get(section, 'password')

        return JiraConfig(url, username, password)


class JiraConfig:
    def __init__(self, url, username, password):
        self.url = url
        self.username = username
        self.password = password


class JiraFactory:
    @classmethod
    def get_sk(cls):
        config = AppConfig.get_jira_config(AppConfig.SK_SECTION)

        return Jira(config.url, basic_auth=(config.username, config.password))

    @classmethod
    def get_pub(cls):
        config = AppConfig.get_jira_config(AppConfig.PUB_SECTION)

        return Jira(config.url, basic_auth=(config.username, config.password))


class Issue(jira.Issue):
    @classmethod
    def parse_key(cls, url):
        r = re.match('^(https?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})\/(browse)\/(?P<key>\w+-\d+)$', url)

        return r.group('key') if r else None

    def external_key(self):
        url = self.external_url()

        return self.parse_key(url) if url else None

    def external_url(self):
        return getattr(self.fields, 'customfield_10105')

    def truncate_summary(self, limit=35):
        """Get truncated summary without key

        :rtype: str
        """
        summary = re.sub('^\w+-\d+:\s*', '', self.fields.summary)

        return summary[:limit] + (summary[limit:] and '..')


class Jira(jira.JIRA):
    def issues_by_worklog_date(self, days_ago):
        result = []
        issues = self.search_issues('worklogDate = startOfDay(-%dd) and worklogAuthor = currentUser()' % days_ago)

        for issue in issues:
            issue.__class__ = Issue
            result.append(issue)

        return issues

    def worklogs_by_date(self, issue, date):
        """Get worklogs and filter them by date

        :rtype: list
        """
        to_datetime = lambda jira_time: dt.strptime(jira_time, '%Y-%m-%dT%H:%M:%S.%f%z').replace(tzinfo=None)

        worklogs = [worklog for worklog in self.worklogs(issue) if
                    to_datetime(worklog.started).date() == date.date()]

        return worklogs

    def timespend(self, issue, date):
        """Get worklog time by date. Returns seconds

        :rtype: int
        """
        return int(sum(worklog.timeSpentSeconds for worklog in self.worklogs_by_date(issue, date)))

    def timezone(self):
        return self.user(self.current_user()).timeZone
