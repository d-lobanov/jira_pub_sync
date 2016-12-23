from datetime import datetime as dt, timedelta as td, timezone
import click
from src.config import Issue, JiraConfig
import re
import jira

class IO:
    STATUS_COLOR = {'info': 'white', 'error': 'red', 'warning': 'yellow', 'success': 'green'}

    @classmethod
    def input_days_ago(cls):
        num = 0
        while num < 1:
            num = click.prompt('Please enter a number of days', type=int)

        date = dt.now(tz=timezone.utc) - td(days=num - 1)

        return date.astimezone()

    @classmethod
    def input_jira_estimate(cls, message):
        while True:
            time = click.prompt(message, type=str)

            r = re.match(r"^(\b(\d+[h|m])\b\s*)+$", time)
            if r is not None:
                return time

    @classmethod
    def input_jira_credentials(cls, url=None, username=None, password=None):
        url = click.prompt('Host url', value_proc=cls.url_validation, default=url)
        username = click.prompt('Username', default=username, type=str)
        password = click.prompt('Password' if password is None else 'Password [hidden]', hide_input=True, type=str,
                                default=password, show_default=False)

        return JiraConfig(url, username, password)

    @classmethod
    def url_validation(cls, url):
        r = re.match("^https?:\/\/[\w\-\.]+\.[a-z]{2,6}\.?(\/[\w\.]*)*\/?$", url)
        if r is None:
            raise click.UsageError('Please, type valid URL')

        return url

    @classmethod
    def highlight_key(cls, url=None, issue=None, color='cyan'):
        if isinstance(issue, jira.Issue):
            url = issue.permalink()

            return url.replace(issue.key, click.style(issue.key, fg=color))

        if isinstance(url, str):
            key = Issue.parse_key(url)

            return url.replace(key, click.style(key, fg=color))

        return None

    @classmethod
    def print_date_line(cls, date, on_nl=True):
        if on_nl:
            click.echo()

        click.echo(date.strftime('%d %B %Y, %A'))

    @classmethod
    def print_time_diff_line(cls, pub_issues, sk_issue, time_diff, status=None):
        hours = str(time_diff / 3600) + 'h'

        if time_diff > 0:
            hours = '+' + hours

        if status is None:
            status = 'error'

            if time_diff == 0:
                status = 'info'
            elif time_diff > 0:
                status = 'success'

        cls.print_time_line(pub_issues, sk_issue, hours, status=status)

    @classmethod
    def print_time_line(cls, pub_issues, sk_issue, message, status='info'):
        pub_issues = pub_issues[:]
        pub_issue = pub_issues.pop(0)

        pub_link = IO.highlight_key(issue=pub_issue)

        sk_link = sk_issue.permalink() if sk_issue is not None else None
        sk_link = IO.highlight_key(url=sk_link)

        color = cls.STATUS_COLOR.get(status, 'reset')

        message = click.style(message, fg=color)

        if sk_issue is not None:
            summary = cls.truncate_summary(sk_issue.fields.summary)
        else:
            summary = cls.truncate_summary(pub_issue.fields.summary)

        click.echo('%s => %s [ %s ] %s' % (pub_link, sk_link, message, cls.truncate_summary(summary)))

        for pub_issue in pub_issues[1:]:
            pub_link = IO.highlight_key(issue=pub_issue)
            click.echo(pub_link)

    @classmethod
    def truncate_summary(self, summary, limit=35):
        """Get truncated summary without key

        :rtype: str
        """
        summary = re.sub('^\w+-\d+:\s*', '', summary)

        return summary[:limit] + (summary[limit:] and '...')

    @classmethod
    def print_dict(cls, d, indent=0):
        for key, value in d.items():
            key = click.style(str(key), fg='blue', bold=True)
            if isinstance(value, dict):
                click.echo('\t' * indent + key + ':')
                cls.print_dict(value, indent + 1)
            else:
                value = str(value).replace('\n', ' ').replace('\r', '')
                value = value[:100] + (value[100:] and '...')

                click.echo('\t' * indent + key + ': ' + value)

    @classmethod
    def success(cls, msg):
        click.echo(click.style(msg, fg='green'))

    @classmethod
    def error(cls, msg):
        click.echo(click.style('ERROR: ', fg='green') + msg)