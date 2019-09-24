import os

import click

from cloudshell.migration.configuration.config import Configuration


class ConfigFlow(object):
    NEW_LINE = os.linesep

    def __init__(self, logger, configuration):
        """

        :param logging.Logger logger:
        :param cloudshell.migration.configuration.config.Configuration configuration:
        """
        self.logger = logger
        self._configuration = configuration

    def get_key_value(self, key):
        value = self._configuration.configuration.get(key)
        return self._format_key(key, value)

    def set_key_value(self, key, value):
        if key in Configuration.DEFAULT_VALUES:
            self._configuration.configuration[key] = str(value)
            self._configuration.save()
        else:
            raise click.UsageError('Configuration key {} does not exist'.format(key))

    # def get_patterns_table_value(self, key):
    #     return self._format_key(key, self._configuration.patterns_table.get(key))
    #
    # def set_patterns_table_value(self, key, value):
    #     self._configuration.patterns_table[key] = value
    #     self._configuration.save()

    def get_config_description(self):
        return self._format_table(self._configuration.configuration)

    # def get_patterns_table_description(self):
    #     return self._format_table(self._configuration.patterns_table)

    @staticmethod
    def _format_key(key, value):
        if key == Configuration.KEY.PASSWORD:
            value = '*' * len(value)
        return '{0}: {1}'.format(key, value)

    def _format_table(self, table):
        """
        :type table: dict
        """
        output = ''
        for key, value in table.iteritems():
            line = self._format_key(key, value)
            if line:
                output += line
                output += self.NEW_LINE
        return output
