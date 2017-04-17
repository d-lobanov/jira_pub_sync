import re
from datetime import datetime as dt, timedelta as td, timezone

import click
from click.exceptions import Abort
from src.config import JiraConfig


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
        if hasattr(issue, 'permalink'):
            url = issue.permalink()

            return url.replace(issue.key, click.style(issue.key, fg=color))

        if isinstance(url, str):
            key = issue.parse_key_from_url(url)

            return url.replace(key, click.style(key, fg=color))

        return None

    @classmethod
    def highlight_time(cls, seconds):
        hours = cls.seconds_to_hours(seconds)

        if seconds > 0:
            status = 'success'
        elif seconds < 0:
            status = 'error'
        else:
            status = 'reset'

        color = cls.STATUS_COLOR.get(status)

        return click.style(hours, fg=color)

    @classmethod
    def echo_date(cls, date, nl=True):
        if nl:
            click.echo()

        click.echo(date.strftime('%d %B %Y, %A'))

    @classmethod
    def seconds_to_hours(cls, seconds):
        hours = seconds / 3600
        hours = ('%f' % hours).rstrip('0').rstrip('.')

        return ('+' if seconds > 0 else '') + hours + 'h'

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
    def error(cls, msg, nl=False):
        if nl:
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
            if lines == ['']:
                raise Abort

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
