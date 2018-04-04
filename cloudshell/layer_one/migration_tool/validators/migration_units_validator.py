from cloudshell.layer_one.migration_tool.validators.resource_validator import ResourceValidator


class MigrationUnitValidator(object):
    def __init__(self, api):
        """
        :type api: cloudshell.api.cloudshell_api.CloudShellAPISession
        """
        self._api = api
        self._resource_validator = ResourceValidator(api)

    def validate(self, migration_unit):
        """
        :type migration_unit: cloudshell.layer_one.migration_tool.entities.migration_unit.MigrationUnit
        """
        if not self._resource_validator.old_resource_is_valid(migration_unit.old_resource):
            self._resource_validator.validate_old_resource(migration_unit.old_resource)

        if not self._resource_validator.new_resource_is_valid(migration_unit.new_resource):
            self._resource_validator.validate_new_resource(migration_unit.old_resource, migration_unit.new_resource)