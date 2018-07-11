from cloudshell.layer_one.migration_tool.entities.config_unit import ConfigUnit
from cloudshell.layer_one.migration_tool.entities.migration_config import MigrationConfig


class MigrationConfigParser(object):
    SEPARATOR = ','

    def __init__(self, logger):
        """
        :type logger: cloudshell.layer_one.migration_tool.helpers.logger.Logger
        """
        self._logger = logger

    def parse_configuration(self, old_resources_str, new_resources_str):
        """
        :type old_resources_str: str
        :type new_resources_str: str
        """
        migration_config_list = []
        old_resources_conf_list = old_resources_str.split(self.SEPARATOR)
        new_resources_conf_list = new_resources_str.split(self.SEPARATOR)

        for index in xrange(len(old_resources_conf_list)):
            if len(new_resources_conf_list) == 1:
                migration_config_list.append(
                    MigrationConfig(ConfigUnit(old_resources_conf_list[index]), ConfigUnit(new_resources_conf_list[0])))
            else:
                migration_config_list.append(
                    MigrationConfig(ConfigUnit(old_resources_conf_list[index]),
                                    ConfigUnit(new_resources_conf_list[index])))

        return migration_config_list
