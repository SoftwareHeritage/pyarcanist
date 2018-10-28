import click
from phabricator import Phabricator

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
@click.pass_context
def pyarc(ctx, verbose):
    """Entry point"""
    global cnx
    ctx.ensure_object(dict)
    ctx.obj['cnx'] = cnx = Phabricator()
    ctx.obj['options'] = options(verbose=verbose)


if __name__ == '__main__':
    pyarc(obj={})
