import configparser

import jira
from click import Abort
from jira import JIRAError

from src.io import IO
from src.config import AppConfig


class BaseFactory(object):
    @classmethod
    def create_jira(cls, config):
        return jira.JIRA(config.url, basic_auth=(config.username, config.password), async=True)


class PubFactory(BaseFactory):
    @classmethod
    def create(cls):
        return cls.create_jira(AppConfig.read_pub_config())


class SkFactory(BaseFactory):
    @classmethod
    def create(cls):
        return cls.create_jira(AppConfig.read_sk_config())


class JiraFactory():
    @classmethod
    def createOrAbort(cls):
        try:
            sk_jira = SkFactory.create()
            pub_jira = PubFactory.create()
        except (configparser.NoSectionError, configparser.NoOptionError):
            IO.error('Can\'t find valid configs. Please, check configs')
            raise Abort()
        except JIRAError:
            IO.error('Can\'t connect to JIRA. Please, check configs')
            raise Abort()

        return sk_jira, pub_jira
