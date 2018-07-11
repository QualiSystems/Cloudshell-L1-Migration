import click


class MigrationOperationValidator(object):
    def __init__(self, api, logger):
        """
        :type api: cloudshell.api.cloudshell_api.CloudShellAPISession
        :type logger: cloudshell.layer_one.migration_tool.helpers.logger.Logger
        """
        self._api = api
        self._logger = logger

    def validate(self, migration_operation):
        """
        :type migration_operation: cloudshell.layer_one.migration_tool.entities.migration_operation.MigrationOperation
        """
        old_resource = migration_operation.old_resource
        old_valid = False
        new_resource = migration_operation.new_resource
        new_valid = False

        if old_resource.exist and self._existing_resource_is_valid(old_resource):
            old_valid = True
        if (not new_resource.exist and self._not_existing_resource_is_valid(new_resource)) or (
                new_resource.exist and self._existing_resource_is_valid(new_resource)):
            new_valid = True
        if old_valid and new_valid:
            migration_operation.valid = True

    def _existing_resource_is_valid(self, resource):
        """
        :type resource: cloudshell.layer_one.migration_tool.entities.resource.Resource
        """
        if resource.name and resource.address:
            return True
        else:
            return False

    def _not_existing_resource_is_valid(self, resource):
        """
        :type resource: cloudshell.layer_one.migration_tool.entities.resource.Resource
        """
        if resource.name and resource.address and resource.family and resource.model and resource.driver:
            return True
        else:
            return False

    def validate_list(self, migration_operation_list):
        """
        :type migration_operation_list: list
        """
        for migration_unit in migration_operation_list:
            self.validate(migration_unit)
        return migration_operation_list
