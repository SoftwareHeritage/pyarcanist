import click
from phabricator import Phabricator


class options(dict):
    def __getattr__(self, key):
        return self[key]

    def __setattr__(self, key, value):
        self[key] = value


@click.group()
@click.option('-v', '--verbose/--no-verbose', default=False, envvar='VERBOSE')
@click.pass_context
def pyarc(ctx, verbose):
    """Entry point"""
    ctx.ensure_object(dict)
    ctx.obj['cnx'] = Phabricator()
    ctx.obj['options'] = options(verbose=verbose)


if __name__ == '__main__':
    pyarc(obj={})
