import click
from . import cache
from . import cli


@cache.cache()
def get_user(phid=None):
    if phid is None:
        return dict(cli.cnx.user.whoami())
    return cli.cnx.phid.query(phids=[phid])[phid]


@cli.pyarc.command()
@click.pass_context
def whoami(ctx):
    '''Gives informations on the current user'''
    user = get_user()
    click.echo("{userName} ({realName})".format(**user))
    options = ctx.obj['options']
    if options.verbose:
        for k in ('phid', 'primaryEmail', 'roles', 'uri'):
            click.echo("  {}: {}".format(k, user[k]))
