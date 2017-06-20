import os

import click

try:
    import ConfigParser as configparser
except ImportError:
    import configparser


class AppConfig:
    SK_SECTION = 'SK_JIRA'
    PUB_SECTION = 'PUB_JIRA'

    HIDDEN_ISSUES = 'HIDDEN_ISSUES'

    APP_NAME = 'JiraPubSync'

    @classmethod
    def get_file_path(cls):
        return os.path.join(cls.get_dir_path(), 'config.ini')

    @classmethod
    def get_dir_path(cls):
        return click.get_app_dir(cls.APP_NAME, False, False)

    @classmethod
    def write_hidden_keys(cls, hidden_keys, rewrite=False):
        config = cls._read()
        if not config.has_section(cls.SK_SECTION):
            config.add_section(cls.SK_SECTION)
        elif not rewrite:
            hidden_keys += cls.read_hidden_keys()

        hidden_keys = map(str, hidden_keys)
        config.set(cls.SK_SECTION, cls.HIDDEN_ISSUES, ','.join((set(hidden_keys))))

        cls._write(config)

    @classmethod
    def read_hidden_keys(cls):
        config = cls._read()

        if config.has_option(cls.SK_SECTION, cls.HIDDEN_ISSUES):
            issues = config.get(cls.SK_SECTION, cls.HIDDEN_ISSUES)

            if issues:
                return issues.split(',')

        return []

    @classmethod
    def read_pub_config(cls):
        try:
            return cls._read_jira_config(cls.PUB_SECTION)
        except:
            return JiraConfig()

    @classmethod
    def read_sk_config(cls):
        try:
            return cls._read_jira_config(cls.SK_SECTION)
        except:
            return JiraConfig()

    @classmethod
    def write_pub_config(cls, jira_config):
        return cls._write_jira_config(cls.PUB_SECTION, jira_config)

    @classmethod
    def write_sk_config(cls, jira_config):
        return cls._write_jira_config(cls.SK_SECTION, jira_config)

    @classmethod
    def _read_jira_config(cls, section):
        config = cls._read()

        url = config.get(section, 'url')
        username = config.get(section, 'username')
        password = config.get(section, 'password')

        return JiraConfig(url, username, password)

    @classmethod
    def _read(cls):
        config = configparser.RawConfigParser()
        config.read([cls.get_file_path()])

        return config

    @classmethod
    def _write(cls, config):
        dir_path = cls.get_dir_path()
        if not os.path.isdir(dir_path):
            os.makedirs(dir_path, exist_ok=True)

        with open(cls.get_file_path(), 'w') as configfile:
            config.write(configfile)

    @classmethod
    def _write_jira_config(cls, section, jira_config):
        config = cls._read()
        if not config.has_section(section):
            config.add_section(section)

        config.set(section, 'url', jira_config.url)
        config.set(section, 'username', jira_config.username)
        config.set(section, 'password', jira_config.password)

        cls._write(config)


class JiraConfig:
    def __init__(self, url=None, username=None, password=None):
        self.url = url
        self.username = username
        self.password = password

    def valid(self):
        return self.url and self.username and self.password
