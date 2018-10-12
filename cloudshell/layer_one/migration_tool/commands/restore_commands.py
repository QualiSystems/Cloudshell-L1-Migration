import yaml

from cloudshell.layer_one.migration_tool.helpers.logical_route_helper import LogicalRouteHelper
from cloudshell.layer_one.migration_tool.helpers.resource_operation_helper import ResourceOperationHelper


class RestoreCommands(object):
    SEPARATOR = ','

    def __init__(self, api, logger, configuration, backup_file):
        self._api = api
        self._logger = logger
        self._configuration = configuration
        self._backup_file = backup_file

        self._resource_operation_helper = ResourceOperationHelper(api, logger, dry_run=False)
        self._logical_route_helper = LogicalRouteHelper(api, logger, dry_run=False)

        self.__logical_routes = []

    @property
    def _active_routes(self):
        if not self.__logical_routes:
            logical_routes = set()
            for routes_list in self._logical_route_helper.logical_routes_by_resource_name.values():
                logical_routes.update(routes_list)
            self.__logical_routes = list(logical_routes)
        return self.__logical_routes

    def _load_backup(self):
        with open(self._backup_file, 'r') as backup_file:
            data = yaml.load(backup_file)
            return data

    def prepare_resources(self, resources_string=None):
        """
        :param resources_string:
        :type resources_string: str
        :return:
        """
        resource_list = self._load_backup()
        resources_by_name = {resource.name: resource for resource in resource_list}
        restore_resources = []
        if resources_string:
            resources_names = resources_string.split(self.SEPARATOR)
            for name in resources_names:
                if name in resources_by_name:
                    restore_resources.append(resources_by_name.get(name))
        else:
            restore_resources = resource_list
        return restore_resources

    def restore(self, resources):
        routes_set = set()
        for resource in resources:
            self._restore_connections(resource)
            routes_set.update(resource.logical_routes)
        self._restore_logical_routes(routes_set)
        # self._replace_with_active(backup_routes)

    # def _cross_active_routes(self, backup_routes):
    #     """
    #     :type backup_routes: list
    #     """
    #     cross_active_routes=[]
    #     for route in backup_routes:
    #         if route in self._active_routes:
    #             cross_active_routes.append(self._active_routes.)
    #         # self._resource_operation_helper.

    # def _active_routes(self, backup_routes):
    #     active_routes = []
    #     for route in self._logical_route_helper.logical_routes_by_resource_name.values():
    #         if route in backup_routes:
    #             active_routes.append(route)
    #     return active_routes

    def _restore_connections(self, resource):
        """
        :param resource:
        :type resource: cloudshell.layer_one.migration_tool.entities.resource.Resource
        :return:
        """
        for connection in resource.connections:
            self._resource_operation_helper.update_connection(connection)

    def _restore_logical_routes(self, logical_routes):
        for logical_route in logical_routes:
            self._logical_route_helper.create_route(logical_route)
