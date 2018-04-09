import click

from cloudshell.layer_one.migration_tool.entities.config_unit import ConfigUnit
from cloudshell.layer_one.migration_tool.entities.migration_config import MigrationConfig
from cloudshell.layer_one.migration_tool.handlers.migration_config_handler import MigrationConfigHandler
from cloudshell.layer_one.migration_tool.handlers.migration_config_parser import MigrationConfigParser
from cloudshell.layer_one.migration_tool.handlers.migration_operation_handler import MigrationOperationHandler
from cloudshell.layer_one.migration_tool.validators.migration_operation_validator import MigrationOperationValidator


class MigrationCommands(object):

    def __init__(self, api):
        self._api = api

    def prepare_operations(self, old_resources, new_resources):
        """
        :type old_resources: str
        :type new_resources: str
        """
        migration_configs_list = MigrationConfigParser.parse_configuration(old_resources, new_resources)
        migration_config_handler = MigrationConfigHandler(self._api)
        operations = migration_config_handler.define_operations_for_list(migration_configs_list)
        # operations_validator = MigrationOperationValidator(self._api)
        # operations = operations_validator.validate_list(operations)
        migration_operations_handler = MigrationOperationHandler(self._api)
        migration_operations_handler.prepare_operation_list(operations)

        return operations



    def format_operations(self, operations):
        return '\n'.join([str(operation) for operation in operations])

    def perform_operations(self, operations):
        operations_handler = MigrationOperationHandler(self._api)
        operations_handler.perform_operation(operations)
