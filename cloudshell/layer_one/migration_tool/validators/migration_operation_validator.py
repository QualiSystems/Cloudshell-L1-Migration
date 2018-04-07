class MigrationUnitValidator(object):
    def __init__(self, api):
        """
        :type api: cloudshell.api.cloudshell_api.CloudShellAPISession
        """
        self._api = api

    def validate(self, migration_operation):
        """
        :type migration_operation: cloudshell.layer_one.migration_tool.entities.migration_operation.MigrationOperation
        """
        return migration_operation

    def validate_list(self, migration_operation_list):
        """
        :type migration_operation_list: list
        """
        for migration_unit in migration_operation_list:
            self.validate(migration_unit)
