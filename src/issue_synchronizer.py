from datetime import datetime as dt

import click

import src.config as config
from src.io import IO as io
from src.jira_container import PubIssue
from src.jira_helper import PubHelper


class IssueSync(object):
    def __init__(self, sk_jira, pub_jira):
        self._sk_jira = sk_jira
        self._pub_jira = pub_jira

        self._pub_helper = PubHelper(pub_jira)

    def migrate(self, sk_key):
        """
        Migrates issue from SK to PUB.
        """
        try:
            sk_issue = self._sk_jira.issue(sk_key)
        except Exception:
            io.error('Can\'t find the issue by key: %s' % sk_key)

            return

        pub_issues = self._pub_jira.search_issues("'External issue ID' ~ '%s'" % sk_issue.permalink())

        if pub_issues:
            click.echo('\nThis task has been already migrated to PUB: ')

            for issue in pub_issues:
                click.echo(io.highlight_key(issue=issue) + '\t' + io.truncate_summary(issue.fields.summary))

            if not click.confirm('\nContinue?', default=False):
                return

        click.echo('Beginning of migration %s' % io.highlight_key(issue=sk_issue))

        pub_issue = self.create_pub_issue(sk_issue)
        if pub_issue is None:
            click.echo('Error has occurred')
            return

        click.echo('Issue was migrated: %s' % io.highlight_key(issue=pub_issue))

        self.migrate_attachments(sk_issue, pub_issue)

        return pub_issue

    def migrate_issues(self, started):
        """
        Migrates issues from SK to PUB.

        :param started:
        :return:
        """
        today = dt.today().replace(tzinfo=started.tzinfo)
        days = int((today - started).days) + 1

        sk_issues = self._sk_jira.search_issues(
            'createdDate >= startOfDay(-%dd) and (assignee=currentUser() or worklogAuthor=currentUser())' % days,
            maxResults=100000)

        pub_issues = self._pub_helper.get_issues_by_sk_links([sk_issue.permalink() for sk_issue in sk_issues])

        exists_sk_links = [PubIssue(issue).sk_url for issue in pub_issues]

        new_issues = [issue for issue in sk_issues if issue.permalink() not in exists_sk_links]

        if not new_issues:
            click.echo('Nothing to do')
            return

        hidden_keys = config.AppConfig.read_hidden_keys()

        new_issues = [issue for issue in new_issues if issue.key not in hidden_keys]

        m_issues, s_issues, h_issues = io.edit_unsync_issues(new_issues)

        h_keys = [h_issue.key for h_issue in h_issues]
        config.AppConfig.write_hidden_keys(h_keys)

        for issue in m_issues:
            self.migrate(issue.key)

    def create_pub_issue(self, sk_issue):
        """
        Migrate SK issue to PUB Jira

        :param sk_issue:
        :return:
        """
        fields = self.convert_fields(sk_issue)

        click.echo("\nPlease confirm migration:")
        io.print_dict(fields, indent=1)

        if not click.confirm('\nMigrate?', default=False):
            return None

        return self._pub_jira.create_issue(fields=fields)

    def migrate_attachments(self, sk_issue, pub_issue):
        """
        Migrate attachments from SK issue to PUB issue

        :param sk_issue:
        :param pub_issue:
        :return:
        """
        if sk_issue.fields.attachment:
            click.echo('Beginning of migration attachments')

        for attachment in sk_issue.fields.attachment:
            self._pub_jira.add_attachment(pub_issue, attachment.get(), filename=attachment.filename)

    def convert_fields(self, sk_issue):
        """
        Convert SK issue to PUB fileds

        :param sk_issue:
        :return:
        """
        click.echo()

        default_summary = sk_issue.key + ': ' + sk_issue.fields.summary
        summary = click.prompt('Summary', default=default_summary, type=str)

        estimate = io.input_jira_estimate('Original Estimate')

        labels = ['auto_migration']

        if sk_issue.fields.project.key == 'ULT':
            labels += ['ultra']

        return {
            'project': {
                'id': '41767',  # Sheknows DT project
                'name': 'SheknowsDT'
            },
            'issuetype': self.convert_issue_type(sk_issue.fields.issuetype),
            'summary': summary,
            'priority': self.convert_priority(sk_issue.fields.priority),
            'description': sk_issue.fields.description if sk_issue.fields.description else summary,
            'timetracking': {
                'originalEstimate': estimate
            },
            'labels': labels,
            'customfield_11470': sk_issue.permalink()
        }

    @classmethod
    def convert_priority(cls, sk_priority):
        """
        Convert SK issue priority to PUB. You can find all of the by /rest/api/2/priority.

        :param sk_priority:
        :return:
        """
        map = {
            1: {  # Blocker
                'id': '1',
                'name': 'Blocker'
            },
            2: {  # Critical
                'id': '2',
                'name': 'Critical'
            },
            3: {  # Major
                'id': '3',
                'name': 'Major'
            },
            7: {  # Important
                'id': '3',
                'name': 'Major'
            },
            4: {  # Minor
                'id': '4',
                'name': 'Minor'
            },
            5: {  # Trivial
                'id': '5',
                'name': 'Trivial'
            },
        }

        return map.get(int(sk_priority.id), map[4])

    @classmethod
    def convert_issue_type(cls, sk_type):
        """
        Convert SK issue type to PUB. You can find all types by /rest/api/2/issuetype.

        :param sk_type:
        :return:
        """
        map = {
            1: {  # Bug
                'id': '1',
                'name': 'Bug',
            },
            3: {  # Task
                'id': '3',
                'name': 'Task',
            },
        }

        return map.get(int(sk_type.id), map[3])
