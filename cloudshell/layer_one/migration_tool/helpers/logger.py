import sys

import click

from cloudshell.layer_one.migration_tool.exceptions import MigrationToolException


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


class ExceptionLogger(object):
    def __init__(self, logger):
        self._logger = logger

    def __enter__(self):
        return self._logger

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type == MigrationToolException:
            self._logger.error(exc_val.message)
            sys.exit(1)
        else:
            return False
