import click

from cloudshell.layer_one.migration_tool.helpers.config_helper import ConfigHelper


class ConfigCommands(object):
    NEW_LINE = '\n'

    def __init__(self, config_helper):
        """
        :type config_helper: cloudshell.layer_one.migration.helpers.config_helper.ConfigHelper
        """
        self._config_helper = config_helper

    def get_key_value(self, key):
        value = self._config_helper.configuration.get(key)
        return self._format_output(key, value)

    def set_key_value(self, key, value):
        if key in ConfigHelper.DEFAULT_CONFIGURATION:
            self._config_helper.configuration[key] = value
            self._config_helper.save()
        else:
            raise click.UsageError('Configuration key {} does not exist'.format(key))

    def get_config_description(self):
        output = ''
        for key, value in self._config_helper.configuration.iteritems():
            output += self._format_output(key, value)
            output += self.NEW_LINE
        return output

    @staticmethod
    def _format_output(key, value):
        if key == ConfigHelper.PASSWORD_KEY:
            value = '*' * len(value)
        return '{0}: {1}'.format(key, value)
