from itertools import chain
from datetime import datetime

import humanize
import click
import git

from . import cli
from .whoami import get_user
from .tools import wrap, object_from_phid
from . import cache


@cache.cache()
def get_repositories(uris):
    if isinstance(uris, str):
        uris = [uris]
    return cli.cnx.diffusion.repository.search(
        constraints={'uris': uris}).data


@cache.cache()
def repo_from_phid(phid):
    repo = cli.cnx.diffusion.repository.search(
        constraints={'phids': [phid]}).data
    return repo and repo[0] or None


def format_diff(kw):
    # warning: this function modifies the given dict 'kw'
    kw['id'] = click.style(str(kw['id']), bold=True)
    kw['fields']['status']['name'] = click.style(
        kw['fields']['status']['name'],
        fg=kw['fields']['status']['color.ansi'])
    for k in kw['fields']:
        if k.startswith('date'):
            kw['fields'][k] = datetime.fromtimestamp(kw['fields'][k])
    return kw


@cli.pyarc.command()
@click.option('-u', '--mine/--all-users', default=False)
@click.option('-A', '--all-repos/--current-repo', default=False)
@click.option('-s', '--summary/--default', default=False)
@click.pass_context
def diff(ctx, mine, all_repos, summary):
    '''List Diffs'''
    cnx = cli.cnx
    user = get_user()
    # options = ctx.obj['options']

    query = {'statuses': ['open()']}
    gitrepo = None
    repos = None
    if not all_repos:
        try:
            gitrepo = git.Repo()
            remotes = list(chain(*(r.urls for r in gitrepo.remotes)))
            repos = get_repositories(remotes)
        except git.InvalidGitRepositoryError:
            pass
    if repos:
        query['repositoryPHIDs'] = [r['phid'] for r in repos]
    if mine:
        query['authorPHIDs'] = [user['phid']]

    # print('query=', query)
    diffs = cnx.differential.revision.search(constraints=query).data

    for diff in sorted(diffs, key=lambda x: int(x['id'])):
        fdiff = format_diff(diff)
        if summary:
            click.echo(
                '{fields[status][name]:25} D{id}: {fields[title]}'.format(
                    **fdiff))
        else:
            click.echo(
                wrap('{fields[status][name]:25} D{id}'.format(
                    **fdiff)))
            # give a bit more informations
            fields = fdiff['fields']
            phrepo = repo_from_phid(fields['repositoryPHID'])['fields']
            author = get_user(fields['authorPHID'])

            click.echo('{key}: {shortName} ({callsign})'.format(
                key=click.style('Repo', fg='yellow'),
                **phrepo))

            click.echo('{key}: {value}'.format(
                key=click.style('Author', fg='yellow'),
                value=author['name']))
            n = datetime.now()
            click.echo('{key}: {value} ago'.format(
                key=click.style('Created', fg='yellow'),
                value=humanize.naturaldelta(n - fields['dateCreated'])))
            click.echo('{key}: {value} ago'.format(
                key=click.style('Modified', fg='yellow'),
                value=humanize.naturaldelta(n - fields['dateModified'])))

            click.secho('Summary:', fg='yellow')
            click.secho('  ' + fields['title'], bold=True)
            click.echo()
            click.echo('\n'.join('  ' + x
                                 for x in fields['summary'].splitlines()))
            click.echo()
