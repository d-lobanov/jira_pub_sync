import jira

from src.config import AppConfig
from src.decorators import except_exception


class BaseFactory(object):
    @classmethod
    def create_jira(cls, config):
        if not config.valid():
            raise Exception

        return jira.JIRA(config.url, basic_auth=(config.username, config.password), validate=True)


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
    @except_exception('Can\'t connect to JIRA. Please, check configs by using `jirapub config` command')
    def create(cls):
        return SkFactory.create(), PubFactory.create()
