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


@cache.cache(expire=300)
def get_diff_parents(phid):
    return [parent['destinationPHID']
            for parent in cli.cnx.edge.search(
            types=['revision.parent'], sourcePHIDs=[phid]).data]


@cache.cache(expire=300)
def get_diff_children(phid):
    return [parent['destinationPHID']
            for parent in cli.cnx.edge.search(
            types=['revision.child'], sourcePHIDs=[phid]).data]


def format_diff(kw):
    # warning: this function modifies the given dict 'kw'
    kw['id'] = click.style(str(kw['id']), bold=True)
    kw['fields']['status']['name'] = click.style(
        kw['fields']['status']['name'], bold=True,
        fg=kw['fields']['status']['color.ansi'])
    makedates(kw)
    return kw


def makedates(kw):
    if isinstance(kw, dict):
        for k, v in kw.items():
            if k.startswith('date') and isinstance(v, int):
                kw[k] = datetime.fromtimestamp(v)
            elif isinstance(v, dict):
                makedates(v)
            elif isinstance(v, list):
                kw[k] = [makedates(x) for x in v]
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
    parents = diff.get('parents')
    if parents:
        click.echo('{key}: {parent:6}'.format(
            key=click.style('Depends on', fg='yellow'),
            parent=', '.join('D{}'.format(diffs[parent]['id'])
                             for parent in parents if parent in diffs),
            ))

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
    if 'transactions' in diff:
        click.secho('Comments:', fg='yellow')
        for comments in (tx['comments'] for tx in diff['transactions']
                         if tx['type'] == 'comment'):
            for comment in comments:
                if comment['removed']:
                    continue
                author = get_user(comment['authorPHID'])['name']
                msg = comment['content']['raw']
                click.secho('%s: ' % author, fg='yellow', bold=True, nl=False)
                click.echo('modified {value} ago'.format(
                    value=humanize.naturaldelta(n - comment['dateModified'])),
                           )
                click.echo('\n'.join('  %s' % line
                                     for line in msg.splitlines()))
                break  # only display the last version of the comment


@cli.pyarc.command()
@click.option('-u', '--mine-only/--all-users', default=False)
@click.option('-A', '--all-repos/--current-repo', default=False)
@click.option('-s', '--summary/--default', default=False)
@click.option('-S', '--stack/--no-stack', default=False)
@click.option('-c', '--comments/--no-comments', default=False)
@click.pass_context
def diff(ctx, mine_only, all_repos, summary, stack, comments):
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
        format_diff(diff)
        fields = diff['fields']
        if stack:
            diff['parents'] = list(get_diff_parents(diff['phid']))
            diff['children'] = list(get_diff_children(diff['phid']))
        if all_repos:
            phrepo = repo_from_phid(fields['repositoryPHID'])['fields']
            diff['repo'] = phrepo['shortName']
        if comments:
            diff['transactions'] = cnx.transaction.search(
                objectIdentifier=diff['phid']).data
        author = get_user(fields['authorPHID'])['name']
        diff['author'] = click.style(
            author, bold=True,
            fg='red' if author == user['userName'] else 'yellow')

        diffs[diff['phid']] = diff
        makedates(diffs)

    for phid in (diff['phid'] for diff in rawdiffs):
        if summary:
            display_diff_summary(diffs, phid, user)
        else:
            display_diff_full(diffs, phid, user)
