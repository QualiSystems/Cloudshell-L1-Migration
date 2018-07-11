import click


class Logger(object):
    DEBUG = 'DEBUG'
    INFO = 'INFO'

    def __init__(self, level=INFO):
        self.level = level

    def info(self, message):
        """
        :type message: str
        """
        click.echo(message)

    def debug(self, message):
        """
        :type message: str
        """
        if self.level.lower() == self.DEBUG.lower():
            click.echo(message)

    def error(self, message):
        """
        :type message: str
        """
        click.echo('ERROR: ' + str(message), err=True)
