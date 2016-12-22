import jira
import click
import os
import re
from datetime import datetime as dt, timezone as tz

try:
    import ConfigParser as configparser
except ImportError:
    import configparser


class AppConfig:
    SK_SECTION = 'SK_JIRA'
    PUB_SECTION = 'PUB_JIRA'
    APP_NAME = 'JiraPubSync'

    @classmethod
    def get_file_path(cls):
        return os.path.join(cls.get_dir_path(), 'config.ini')

    @classmethod
    def get_dir_path(cls):
        return click.get_app_dir(cls.APP_NAME, False, False)

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
    def read_jira_config(cls, section):
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
    def create(cls, config):
        return Jira(config.url, basic_auth=(config.username, config.password))

    @classmethod
    def create_sk(cls):
        config = AppConfig.read_jira_config(AppConfig.SK_SECTION)

        return cls.create(config)

    @classmethod
    def create_pub(cls):
        config = AppConfig.read_jira_config(AppConfig.PUB_SECTION)

        return cls.create(config)


class Issue(jira.Issue):
    """ Jira Issue """

    def __init__(self, *args):
        super().__init__(*args)

        self.worklogs = []

    @classmethod
    def parse_key(cls, url):
        r = re.match('^(https?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})\/(browse)\/(?P<key>\w+-\d+)$', url)

        return r.group('key') if r else None

    @property
    def external_key(self):
        url = self.external_url

        return self.parse_key(url) if url else None

    @property
    def external_url(self):
        return getattr(self.fields, 'customfield_10105')

    @property
    def spent_time(self):
        return sum(int(worklog.timeSpentSeconds) for worklog in self.worklogs)


class Jira(jira.JIRA):
    def issues_by_worklog_date(self, date):
        """
        :type date: dt

        :rtype: ReslutList
        """

        result = []

        today = dt.today().replace(tzinfo=date.tzinfo)
        days_ago = int((today - date).days)

        issues = self.search_issues('worklogDate = startOfDay(-%dd) and worklogAuthor=currentUser()' % days_ago)

        for issue in issues:
            issue.__class__ = Issue
            result.append(issue)

        return issues

    def worklogs_by_date(self, issue, date):
        """Get worklogs and filter them by date

        :type date: dt

        :rtype: list
        """
        worklogs = [worklog for worklog in self.worklogs(issue) if
                    self.jira_time_to_dt(worklog.started).date() == date.date()
                    and worklog.author.name == self.current_user()]

        return worklogs

    def remove_worklog(self, issue, worklog):
        url = self._get_url('issue/{0}/worklog/{1}'.format(issue.id, worklog.id))

        self._session.delete(url)

        return True

    def timezone(self):
        """
        Get current User timezone

        :return:
        """
        return self.user(self.current_user()).timeZone

    @classmethod
    def jira_time_to_dt(self, jira_time):
        return dt.strptime(jira_time, '%Y-%m-%dT%H:%M:%S.%f%z').astimezone(tz.utc)
