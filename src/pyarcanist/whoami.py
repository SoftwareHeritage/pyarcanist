import click
from .cli import pyarc


def get_user(cnx):
    return cnx.user.whoami()


@pyarc.command()
@click.pass_context
def whoami(ctx):
    '''Gives informations on the current user'''
    user = get_user(ctx.obj['cnx'])
    click.echo("{userName} ({realName})".format(**user))
    options = ctx.obj['options']
    if options.verbose:
        for k in ('phid', 'primaryEmail', 'roles', 'uri'):
            click.echo("  {}: {}".format(k, user[k]))
