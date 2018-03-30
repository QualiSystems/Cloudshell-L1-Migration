import click


@click.group()
def cli():
    pass


@cli.command()
def version():
    """
    Displays the shellfoundry version
    """
    click.echo(u'shellfoundry version ')


@cli.command()
@click.option(u'--gen2', 'default_view', flag_value='QQ', help="Show 2nd generation shell templates")
@click.option(u'--gen1', 'default_view', flag_value='BB', help="Show 1st generation shell templates")
def list(default_view):
    pass