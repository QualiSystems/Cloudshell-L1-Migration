from cloudshell.layer_one.migration_tool.helpers.connection_associator import ConnectionAssociator
from cloudshell.layer_one.migration_tool.helpers.connection_helper import ConnectionHelper
from cloudshell.layer_one.migration_tool.helpers.logical_route_helper import LogicalRouteHelper
from cloudshell.layer_one.migration_tool.helpers.resource_operation_helper import ResourceOperationHelper
from cloudshell.layer_one.migration_tool.validators.migration_operation_validator import MigrationOperationValidator


class MigrationOperationHandler(object):
    def __init__(self, api, logger):
        """
        :type api: cloudshell.api.cloudshell_api.CloudShellAPISession
        :type logger: cloudshell.layer_one.migration_tool.helpers.logger.Logger
        """
        self._api = api
        self._logger = logger
        self._resource_handler = ResourceOperationHelper(api, logger)
        self._connection_helper = ConnectionHelper(api, logger)
        self._operation_validator = MigrationOperationValidator(self._api, logger)
        self._logical_route_helper = LogicalRouteHelper(api, logger)

    def prepare_operation(self, operation):
        """
        :type operation: cloudshell.layer_one.migration_tool.entities.migration_operation.MigrationOperation
        """
        self._operation_validator.validate(operation)

        self._resource_handler.define_resource_attributes(operation.old_resource)
        if operation.new_resource.exist:
            self._resource_handler.define_resource_attributes(operation.new_resource)
        else:
            operation.new_resource.address = operation.old_resource.address
            operation.new_resource.attributes = operation.old_resource.attributes

        operation.connections = self._resource_handler.define_physical_connections(operation.old_resource)
        operation.logical_routes = self._logical_route_helper.get_logical_routes(operation.connections)

    def perform_operation(self, operation):
        """
        :type operation: cloudshell.layer_one.migration_tool.entities.migration_operation.MigrationOperation
        """
        new_resource = operation.new_resource
        # Remove logical routes associated with this resource
        for logical_route in operation.logical_routes:
            self._logical_route_helper.remove_route(logical_route)

        if not new_resource.exist:
            self._resource_handler.create_resource(new_resource)
            self._resource_handler.autoload_resource(new_resource)
        else:
            self._resource_handler.sync_from_device(new_resource)

        connection_associator = ConnectionAssociator(self._resource_handler.get_resource_ports(new_resource),
                                                     self._logger)

        # Associate connection and reconnect resource ports
        self._logger.debug('Updating connections for resource {}'.format(new_resource))
        for connection in operation.connections:
            self._connection_helper.update_connection(connection_associator.associated_connection(connection))

        # Create logical routes associated with this resource
        for logical_route in operation.logical_routes:
            self._logical_route_helper.create_route(logical_route)
