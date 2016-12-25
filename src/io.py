import re
from datetime import datetime as dt, timedelta as td, timezone

import click
import jira
from click.exceptions import Abort

from src.config import Issue, JiraConfig


class InputException(Exception):
    def __init__(self, message):
        self.message = message


class IO:
    STATUS_COLOR = {'info': 'white', 'error': 'red', 'warning': 'yellow', 'success': 'green'}

    @classmethod
    def input_days_ago(cls, default=None):
        num = 0
        while num < 1:
            num = click.prompt('Please enter a number of days', type=int, default=default)

        date = dt.now(tz=timezone.utc) - td(days=num - 1)

        return date.astimezone()

    @classmethod
    def input_jira_estimate(cls, message):
        while True:
            time = click.prompt(message, type=str)

            r = re.match(r"^(\b(\d+[whm])\b\s*)+$", time)
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

        last_index = len(pub_issues) - 1
        for n, pub_issue in enumerate(pub_issues):
            pub_link = IO.highlight_key(issue=pub_issue)
            postfix = ' /' if last_index == n else ' |'

            click.echo(pub_link + postfix)

    @classmethod
    def truncate_summary(cls, summary, limit=35):
        """Get truncated summary without key

        :rtype: str
        """
        return cls.truncate_text(re.sub('^\w+-\d+:\s*', '', summary), limit)

    @classmethod
    def truncate_text(cls, text, limit=50):
        return text[:limit] + (text[limit:] and '...')

    @classmethod
    def print_dict(cls, d, indent=0):
        for key, value in d.items():
            key = click.style(str(key), fg='blue', bold=True)
            if isinstance(value, dict):
                click.echo('\t' * indent + key + ':')
                cls.print_dict(value, indent + 1)
            else:
                value = str(value).replace('\n', ' ').replace('\r', '')

                click.echo('\t' * indent + key + ': ' + cls.truncate_text(value, 100))

    @classmethod
    def success(cls, msg):
        click.echo(click.style(msg, fg='green'))

    @classmethod
    def error(cls, msg, on_new_line=False):
        if on_new_line:
            click.echo()

        click.echo(click.style('ERROR: ', fg='red') + msg)

    @classmethod
    def edit_unsync_issues(cls, issues):
        def line_format(flag, issue, max_summary):
            summary = cls.truncate_text(issue.fields.summary, max_summary)
            summary = summary.ljust(max_summary + 2)

            return flag + '  ' + issue.key + '\t' + summary + '  ' + issue.permalink()

        MARKER = """
# Commands:
# m = migrate issue.
# s = skip issue for this time (also you can just remove the line).
# h = hide issue (skip and not migrate in future).
        """

        max_summary = max([len(issue.fields.summary) for issue in issues])
        max_summary = max_summary if max_summary < 200 else 200

        items = [line_format('m', issue, max_summary) for issue in issues]

        while True:
            message = click.edit("\n".join(items) + '\n\n' + MARKER)

            if message is None:
                raise Abort

            lines = message.split(MARKER, 1)[0].rstrip('\n').split('\n')

            try:
                return cls._get_unsync_issues(lines, issues)
            except InputException as e:
                cls.error(e.message, on_new_line=True)
                click.pause()

                continue

    @classmethod
    def _get_unsync_issues(cls, lines, issues):
        result = {'m': [], 's': [], 'h': []}

        for num, line in enumerate(lines):
            r = re.match(r"(?P<mode>m|s|h)\s*(?P<key>\w+-\d+)\b.*", line)
            if r is None:
                raise InputException('Invalid line #%s' % str(num + 1))

            key = r.group('key')
            issue = next((issue for issue in issues if issue.key == key), None)

            if issue is None:
                raise InputException('Can\'t find issue by key % s' % key)

            result[r.group('mode')].append(issue)
            issues.remove(issue)

        result['s'] += issues

        return result['m'], result['s'], result['h']