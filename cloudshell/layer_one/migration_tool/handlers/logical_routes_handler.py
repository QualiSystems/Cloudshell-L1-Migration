from cloudshell.layer_one.migration_tool.helpers.logical_route_helper import LogicalRouteHelper


class LogicalRoutesHandler(object):
    def __init__(self, api, logger, dry_run):
        """
        :type api: cloudshell.api.cloudshell_api.CloudShellAPISession
        :type logger: cloudshell.layer_one.migration_tool.helpers.logger.Logger
        """
        self._api = api
        self._logger = logger
        self._logical_route_helper = LogicalRouteHelper(api, logger, dry_run)

    def _get_routes_for_resource(self, resource):
        """
        :type resource: cloudshell.layer_one.migration_tool.entities.resource.Resource
        """
        return self._logical_route_helper.logical_routes_by_resource_name.get(resource.name, set())

    def remove_logical_routes(self, logical_routes):
        # Remove logical routes associated with this resource
        for logical_route in logical_routes:
            self._logical_route_helper.remove_route(logical_route)

    def create_logical_routes(self, logical_routes):
        # Create logical routes associated with this resource
        for logical_route in logical_routes:
            self._logical_route_helper.create_route(logical_route)

    def get_logical_routes(self, operations):
        logical_routes_set = set()
        for operation in operations:
            dd = self._get_routes_for_resource(operation.old_resource)
            logical_routes_set = logical_routes_set | dd
        return logical_routes_set
