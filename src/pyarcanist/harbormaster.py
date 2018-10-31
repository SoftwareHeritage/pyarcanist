import click
from . import cli


validators = {
    'unit': [
        ('name', True, None),
        ('result', True,
         ('pass', 'fail', 'skip', 'broken', 'unsound')),
        ('namespace', False, None),
        ('engine', False, None),
        ('duration', False, float),
        ('path', False, None),
        ('coverage', False, None),
        ('details', False, None),
        ('format', False, None),
    ],
    'lint': [
        ('name', True, None),
        ('code', True, None),
        ('severity', True,
         ('advice', 'autofix', 'warning', 'error', 'disabled')),
        ('path', True, None),
        ('line', False, int),
        ('char', False, int),
        ('description', False, None),
    ],
}


def check_validator(validator, value):
    if not validator:
        return True
    if isinstance(validator, tuple):
        return value in validator
    if callable(validator):
        try:
            validator(value)
        except Exception:
            return False
    return True


def validate(params, report_type):
    if isinstance(params, str):
        params = dict(x.strip().split('=', 1) for x in params.split(','))
    for k, mandatory, validator in validators[report_type]:
        if mandatory and not k in params:
            raise ValueError(
                'Parameter {} is mandatory for a {} report'.format(
                    k, report_type))
        if k in params and not check_validator(validator, params[k]):
            raise ValueError(
                'Parameter {} has an invalid value "{}"'.format(k, params[k]))
    return params


@cli.pyarc.command()
@click.argument('message-type', type=click.Choice(['pass', 'fail', 'work']))
@click.argument('phid')
@click.option('-u', '--unit', multiple=True)
@click.option('-l', '--lint', multiple=True)
@click.pass_context
def send_message(ctx, message_type, phid, unit, lint):
    '''Send a harbormaster message'''

    options = ctx.obj['options']

    kw = {'type': message_type,
          'buildTargetPHID': phid}
    try:
        if unit:
            kw['unit'] = [validate(u, 'unit') for u in unit]
        if lint:
            kw['lint'] = [validate(l, 'lint') for l in lint]
    except ValueError as e:

        ctx.fail('Invalid parameter: {}'. format(e))

    if options.verbose:
        click.echo('Sending message to harbormaster:')
        for k, v in kw.items():
            click.echo("  {}: {}".format(k, v))
    cli.cnx.harbormaster.sendmessage(**kw)
