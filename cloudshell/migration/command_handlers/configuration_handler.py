import os

import click

from cloudshell.migration.operations.config_operations import ConfigOperations


class ConfigurationHandler(object):
    NEW_LINE = os.linesep

    def __init__(self, config_operations):
        """
        :type config_operations: cloudshell.migration.operations.config_operations.ConfigOperations
        """
        self._config_operations = config_operations

    def get_key_value(self, key):
        value = self._config_operations.configuration.get(key)
        return self._format_key(key, value)

    def set_key_value(self, key, value):
        if key in ConfigOperations.DEFAULT_CONFIGURATION:
            self._config_operations.configuration[key] = value
            self._config_operations.save()
        else:
            raise click.UsageError('Configuration key {} does not exist'.format(key))

    # def get_patterns_table_value(self, key):
    #     return self._format_key(key, self._config_operations.patterns_table.get(key))
    #
    # def set_patterns_table_value(self, key, value):
    #     self._config_operations.patterns_table[key] = value
    #     self._config_operations.save()

    def get_config_description(self):
        return self._format_table(self._config_operations.configuration)

    # def get_patterns_table_description(self):
    #     return self._format_table(self._config_operations.patterns_table)

    @staticmethod
    def _format_key(key, value):
        if key == ConfigOperations.KEY.PASSWORD:
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
