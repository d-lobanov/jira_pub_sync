import click
from click.exceptions import Abort

from src.io import IO as io


def except_exception(message=None):
    def decorator(fn):
        def wrapped(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except Exception as e:
                if message is None:
                    io.error(str(e))
                else:
                    io.error(message)

                exit()

        return wrapped

    return decorator


def except_abort(fn):
    def wrapped(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Abort as e:
            click.echo('\nCanceled by user')
            exit()

    return wrapped
