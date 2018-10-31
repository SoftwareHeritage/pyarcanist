import sys
import click
import hashlib

from phabricator import Phabricator

from . import cache

# we use a global variable to store the Phabricator instance so we do not
# have to add the cnx argument to several utility functions which can then
# be cached by beaker. Not very elegent but it works.
cnx = None


class options(dict):
    def __getattr__(self, key):
        return self[key]

    def __setattr__(self, key, value):
        self[key] = value


@click.group()
@click.option('-v', '--verbose/--no-verbose', default=False, envvar='VERBOSE')
@click.option('-h', '--host', default=None, envvar='PHAB_CONDUIT_URL')
@click.option('-t', '--token', default=None, envvar='PHAB_CONDUIT_TOKEN')

@click.pass_context
def pyarc(ctx, verbose, host, token):
    """Entry point"""
    global cnx
    ctx.ensure_object(dict)
    kwargs = {}
    if host:
        kwargs['host'] = host
    if token:
        kwargs['token'] = token
    if host or token:
        hkey = hashlib.sha256('{}:{}'.format(
            host or '', token or '').encode()).hexdigest()
        cache.kwargs['data_dir'] += '/{}'.format(hkey)
    ctx.obj['cnx'] = cnx = Phabricator(**kwargs)
    ctx.obj['options'] = options(verbose=verbose, host=host, token=token)
    if verbose:
        click.echo('Connecting to:')
        click.echo('  API endpoint: {}'.format(cnx.host))
        click.echo('  Token: {}'.format(cnx.token))


if __name__ == '__main__':
    pyarc(obj={})
