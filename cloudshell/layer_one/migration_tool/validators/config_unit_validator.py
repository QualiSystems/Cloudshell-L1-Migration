class ConfigUnitValidator(object):
    def __init__(self, logger):
        """
        :type logger: cloudshell.layer_one.migration_tool.helpers.logger.Logger
        """
        self._logger = logger

    def validate_name(self, config_unit):
        """
        :type config_unit: cloudshell.layer_one.migration_tool.entities.config_unit.ConfigUnit
        """
        return config_unit

    def validate_family(self, config_unit):
        """
        :type config_unit: cloudshell.layer_one.migration_tool.entities.config_unit.ConfigUnit
        """

        return config_unit

    def validate_model(self, config_unit):
        """
        :type config_unit: cloudshell.layer_one.migration_tool.entities.config_unit.ConfigUnit
        """

        return config_unit

    def validate_driver(self, config_unit):
        """
        :type config_unit: cloudshell.layer_one.migration_tool.entities.config_unit.ConfigUnit
        """

        return config_unit

    def validate_old(self, config_unit):
        """
        :type config_unit: cloudshell.layer_one.migration_tool.entities.config_unit.ConfigUnit
        """
        config_unit.valid = True

    def validate_new(self, config_unit):
        """
        :type config_unit: cloudshell.layer_one.migration_tool.entities.config_unit.ConfigUnit
        """
        config_unit.valid = True
