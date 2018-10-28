from itertools import chain
import click
import git
from .cli import pyarc
from .whoami import get_user
from .tools import wrap, object_from_phid


def get_repositories(cnx, uris):
    if isinstance(uris, str):
        uris = [uris]
    return cnx.diffusion.repository.search(
        constraints={'uris': uris}).data


def repo_from_phid(cnx, phid):
    repo = cnx.diffusion.repository.search(
        constraints={'phids': [phid]}).data
    return repo and repo[0] or None


def format_diff(kw):
    kw = kw.copy()
    kw['id'] = click.style(str(kw['id']), bold=True)
    kw['fields']['status']['name'] = click.style(
        kw['fields']['status']['name'],
        fg=kw['fields']['status']['color.ansi'])
    return kw


@pyarc.command()
@click.option('-u', '--mine/--all-users', default=False)
@click.option('-A', '--all-repos/--current-repo', default=False)
@click.option('-s', '--summary/--default', default=False)
@click.pass_context
def diff(ctx, mine, all_repos, summary):
    '''List Diffs'''
    cnx = ctx.obj['cnx']
    user = get_user(cnx)
    # options = ctx.obj['options']

    query = {'statuses': ['open()']}
    gitrepo = None
    repos = None
    if not all_repos:
        try:
            gitrepo = git.Repo()
            remotes = list(chain(*(r.urls for r in gitrepo.remotes)))
            repos = get_repositories(cnx, remotes)
        except git.InvalidGitRepositoryError:
            pass
    if repos:
        query['repositoryPHIDs'] = [r['phid'] for r in repos]
    if mine:
        query['authorPHIDs'] = [user.phid]

    # print('query=', query)
    diffs = cnx.differential.revision.search(constraints=query).data

    for diff in sorted(diffs, key=lambda x: int(x['id'])):
        fields = diff['fields']
        if summary:
            click.echo(
                '{fields[status][name]:25} D{id}: {fields[title]}'.format(
                    **format_diff(diff)))
        else:
            click.echo(
                wrap('{fields[status][name]:25} D{id}'.format(
                    **format_diff(diff))))
            # give a bit more informations
            phrepo = repo_from_phid(cnx, fields['repositoryPHID'])['fields']
            author = object_from_phid(cnx, fields['authorPHID'])
            click.echo('{key}: {shortName} ({callsign})'.format(
                key=click.style('Repo', fg='yellow'),
                **phrepo))
            click.echo('{key}: {value}'.format(
                key=click.style('Author', fg='yellow'),
                value=author['name']))
            click.secho('Summary:', fg='yellow')
            click.secho('  ' + fields['title'], bold=True)
            click.echo()
            click.echo('\n'.join('  ' + x
                                 for x in fields['summary'].splitlines()))
            click.echo()
