from copy import copy

import yaml

from cloudshell.layer_one.migration_tool.exceptions import MigrationToolException
from cloudshell.layer_one.migration_tool.operations.argument_parser import ArgumentParser
from cloudshell.layer_one.migration_tool.operations.logical_route_operations import LogicalRouteOperations
from cloudshell.layer_one.migration_tool.operations.resource_operations import ResourceOperations


class RestoreCommands(object):
    SEPARATOR = ','

    def __init__(self, api, logger, configuration, backup_file):
        self._api = api
        self._logger = logger
        self._configuration = configuration
        self._backup_file = backup_file

        self._logical_route_helper = LogicalRouteOperations(api, logger, dry_run=False)
        self._resource_operations = ResourceOperations(api, logger)

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

    def initialize_resources(self, resources_arguments, connections, routes, override):

        if not connections and not routes:
            connections = routes = True

        requested_resources = self._requested_resources(resources_arguments)
        backup_resources = self._load_backup()
        requested_backup_resources = []
        if requested_resources:
            for resource in requested_resources:
                if resource not in backup_resources:
                    raise MigrationToolException('Requested resource {} is not in the backup file'.format(resource))
                requested_backup_resources.append(backup_resources[backup_resources.index(resource)])
        else:
            requested_backup_resources = backup_resources

        requested_cs_resources = map(lambda x: self._resource_operations.update_details(copy(x)), requested_backup_resources)
        print(cs_resources)

    def _prepare_actions(self):
        pass

    def _define_connections_operations(self, backup_resource, cs_resource, override):
        """
        :type backup_resource: cloudshell.layer_one.migration_tool.entities.Resource
        :type cs_resource: cloudshell.layer_one.migration_tool.entities.Resource
        :type override: bool
        """
        if len(backup_resource.ports) != len(cs_resource.ports):
            raise MigrationToolException('Number of ports for resource {} does not match'.format(backup_resource))
        for backup_port, cs_port in zip(backup_resource.ports, cs_resource.ports):
            if backup_port.connected_to != cs_port.connected_to:




    def _requested_resources(self, resources_arguments):
        """
        :type resources_arguments: str
        """
        config_resources = []
        for config_unit in ArgumentParser(self._logger).parse_argument_string(resources_arguments):
            config_resources.extend(self._resource_operations.initialize(config_unit))
        return config_resources

    def restore(self, resources):
        routes_set = set()
        for resource in resources:
            self._restore_connections(resource)
            routes_set.update(resource.logical_routes)
        self._restore_logical_routes(routes_set)
        # self._replace_with_active(backup_routes)
