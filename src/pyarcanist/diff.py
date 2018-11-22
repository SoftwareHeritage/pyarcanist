from itertools import chain
from datetime import datetime

import humanize
import click
import git

from . import cli
from .whoami import get_user
from .tools import wrap
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


def get_diff_parents(phid):
    for parent in cli.cnx.edge.search(
            types=['revision.parent'], sourcePHIDs=[phid]).data:
        yield parent['destinationPHID']


def get_diff_children(phid):
    for parent in cli.cnx.edge.search(
            types=['revision.child'], sourcePHIDs=[phid]).data:
        yield parent['destinationPHID']


def format_diff(kw):
    # warning: this function modifies the given dict 'kw'
    kw['id'] = click.style(str(kw['id']), bold=True)
    kw['fields']['status']['name'] = click.style(
        kw['fields']['status']['name'], bold=True,
        fg=kw['fields']['status']['color.ansi'])
    for k in kw['fields']:
        if k.startswith('date'):
            kw['fields'][k] = datetime.fromtimestamp(kw['fields'][k])
    return kw


def display_diff_summary(diffs, phid, user):
    diff = diffs[phid]
    tmpl = ['D{id}']
    if 'repo' in diff:
        tmpl.append('{repo:16}')
    tmpl.append('{fields[status][name]:25}')
    if 'repo' in diff:
        if 'author' in diff:
            tmpl.append('{author:12}')
        tmpl.append('\n\t')
    tmpl.append('{fields[title]}')
    click.echo(' '.join(tmpl).format(**diff))


def display_diff_full(diffs, phid, user):
    diff = diffs[phid]
    fields = diff['fields']

    click.echo(
        wrap('{fields[status][name]:25} D{id}'.format(
            **diff)))
    # give a bit more informations
    phrepo = repo_from_phid(fields['repositoryPHID'])['fields']

    click.echo('{key}: {shortName} ({callsign})'.format(
        key=click.style('Repo', fg='yellow'),
        **phrepo))

    click.echo('{key}: {value}'.format(
        key=click.style('Author', fg='yellow'),
        value=diff['author']))

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


@cli.pyarc.command()
@click.option('-u', '--mine-only/--all-users', default=False)
@click.option('-A', '--all-repos/--current-repo', default=False)
@click.option('-s', '--summary/--default', default=False)
@click.option('-S', '--stack/--no-stack', default=False)
@click.pass_context
def diff(ctx, mine_only, all_repos, summary, stack):
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
    if mine_only:
        query['authorPHIDs'] = [user['phid']]

    rawdiffs = cnx.differential.revision.search(constraints=query).data
    rawdiffs.sort(key=lambda x: int(x['id']))
    diffs = {}

    for diff in rawdiffs:
        fdiff = format_diff(diff)
        fields = fdiff['fields']
        if stack:
            fdiff['parents'] = list(get_diff_parents(diff['phid']))
            fdiff['children'] = list(get_diff_children(diff['phid']))
        if all_repos:
            phrepo = repo_from_phid(fields['repositoryPHID'])['fields']
            fdiff['repo'] = phrepo['shortName']
        author = get_user(fields['authorPHID'])['name']
        fdiff['author'] = click.style(
            author, bold=True,
            fg='red' if author == user['userName'] else 'yellow')

        diffs[diff['phid']] = diff

    for phid in (diff['phid'] for diff in rawdiffs):
        if summary:
            display_diff_summary(diffs, phid, user)
        else:
            display_diff_full(diffs, phid, user)
