import jira

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
