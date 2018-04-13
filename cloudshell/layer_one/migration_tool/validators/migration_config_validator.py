from cloudshell.layer_one.migration_tool.validators.config_unit_validator import ConfigUnitValidator


class MigrationConfigValidator(object):
    def __init__(self, logger):
        """
        :type logger: cloudshell.layer_one.migration_tool.helpers.logger.Logger
        """
        self._logger = logger
        self._config_unit_validator = ConfigUnitValidator(logger)

    def validate(self, config):
        """
        :type config: cloudshell.layer_one.migration_tool.entities.migration_config.MigrationConfig
        """
        self._config_unit_validator.validate_old(config.old_config)
        self._config_unit_validator.validate_new(config.new_config)
        if config.old_config.valid and config.new_config.valid:
            config.valid = True
