from cloudshell.layer_one.migration_tool.entities.migration_operation import MigrationOperation
from cloudshell.layer_one.migration_tool.helpers.resource_operation_helper import ResourceOperationHelper


class MigrationOperationHandler(object):
    def __init__(self, api):
        self._api = api
        self._resource_handler = ResourceOperationHelper(api)

    def prepare_operation(self, operation):
        """
        :type operation: cloudshell.layer_one.migration_tool.entities.migration_operation.MigrationOperation
        """
        # for operation in operations:
        logical_routes = self._resource_handler.get_logical_routes(operation.old_resource)
        #     phisical_routes = self._resource_handler.get_physical_connections(operation.old_resource)

    def prepare_operation_list(self, operation_list):
        for operation in operation_list:
            self.prepare_operation(operation)
        return operation_list


    def _define_resource_attributes(self, resource):
        pass

    def _define_resource_logical_routes(self, resource):
        pass

    def _define_physical_connections(self, resource):
        pass

        