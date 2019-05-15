import os

import click

from cloudshell.layer_one.migration_tool.helpers.config_helper import ConfigHelper


class ConfigurationHandler(object):
    NEW_LINE = os.linesep

    def __init__(self, config_helper):
        """
        :type config_helper: cloudshell.layer_one.migration_tool.helpers.config_helper.ConfigHelper
        """
        self._config_helper = config_helper

    def get_key_value(self, key):
        value = self._config_helper.configuration.get(key)
        return self._format_key(key, value)

    def set_key_value(self, key, value):
        if key in ConfigHelper.DEFAULT_CONFIGURATION:
            self._config_helper.configuration[key] = value
            self._config_helper.save()
        else:
            raise click.UsageError('Configuration key {} does not exist'.format(key))

    # def get_patterns_table_value(self, key):
    #     return self._format_key(key, self._config_helper.patterns_table.get(key))
    #
    # def set_patterns_table_value(self, key, value):
    #     self._config_helper.patterns_table[key] = value
    #     self._config_helper.save()

    def get_config_description(self):
        return self._format_table(self._config_helper.configuration)

    # def get_patterns_table_description(self):
    #     return self._format_table(self._config_helper.patterns_table)

    @staticmethod
    def _format_key(key, value):
        if key == ConfigHelper.PASSWORD_KEY:
            value = '*' * len(value)
        elif key == ConfigHelper.ASSOCIATIONS_TABLE_KEY:
            return
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
