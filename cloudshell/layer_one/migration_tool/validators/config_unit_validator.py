class ConfigUnitValidator(object):
    def __init__(self, api):
        self._api = api

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
