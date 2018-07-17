import click

from cloudshell.layer_one.migration_tool.entities.config_unit import ConfigUnit
from cloudshell.layer_one.migration_tool.entities.migration_config import MigrationConfig
from cloudshell.layer_one.migration_tool.handlers.config_handler import ConfigHandler
from cloudshell.layer_one.migration_tool.handlers.logical_routes_handler import LogicalRoutesHandler
from cloudshell.layer_one.migration_tool.handlers.migration_operation_handler import MigrationOperationHandler
from cloudshell.layer_one.migration_tool.helpers.config_helper import ConfigHelper
from cloudshell.layer_one.migration_tool.validators.migration_config_validator import MigrationConfigValidator
from cloudshell.layer_one.migration_tool.validators.migration_operation_validator import MigrationOperationValidator


class MigrationCommands(object):

    def __init__(self, api, logger, configuration, dry_run):
        """
        :type api: cloudshell.api.cloudshell_api.CloudShellAPISession
        :type logger: cloudshell.layer_one.migration_tool.helpers.logger.Logger
        """
        self._api = api
        self._logger = logger
        self._configuration = configuration
        self._dri_run = dry_run
        self._config_handler = ConfigHandler(self._api, self._logger,
                                             self._configuration.get(ConfigHelper.NEW_RESOURCE_NAME_PREFIX))
        self._operation_handler = MigrationOperationHandler(self._api, self._logger, configuration, dry_run)
        # self._logical_routes_handler = LogicalRoutesHandler(self._api, self._logger, dry_run)

    def prepare_configs(self, old_resources, new_resources):
        config_validator = MigrationConfigValidator(self._logger)
        configs = self._config_handler.parse_migration_configuration(old_resources, new_resources)
        for config in configs:
            config_validator.validate(config)
        return configs

    def prepare_operations(self, migration_configs):
        """
        :type migration_configs: list
        """

        operations_list = []
        for migration_config in migration_configs:
            operations_list.extend(self._config_handler.define_migration_operations(migration_config))

        operation_validator = MigrationOperationValidator(self._api, self._logger)
        for operation in operations_list:
            self._operation_handler.prepare_operation(operation)
            operation_validator.validate(operation)
            if operation.valid:
                self._operation_handler.define_connections(operation)
        return operations_list

    def perform_operations(self, operations):
        for operation in operations:
            if operation.valid:
                # try:
                self._operation_handler.perform_operation(operation)
                # except Exception as e:
                #     operation.success = False
                #     self._logger.error('Error: '.format(str(e)))
