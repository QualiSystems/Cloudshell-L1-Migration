from cloudshell.layer_one.migration_tool.entities.config_unit import ConfigUnit


class MigrationConfig(object):

    def __init__(self, old_config, new_config):
        """
        :type old_config: cloudshell.layer_one.migration_tool.entities.config_unit.ConfigUnit
        :type new_config: cloudshell.layer_one.migration_tool.entities.config_unit.ConfigUnit
        """
        self.old_config = old_config
        self.new_config = new_config
        self.valid = False
