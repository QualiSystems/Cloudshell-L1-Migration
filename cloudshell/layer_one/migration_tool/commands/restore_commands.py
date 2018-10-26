from copy import copy

import yaml

from cloudshell.layer_one.migration_tool.actions import RemoveRouteAction, CreateRouteAction, UpdateConnectionAction, \
    ActionsContainer
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

        self._logical_route_operations = LogicalRouteOperations(api, logger, dry_run=False)
        self._resource_operations = ResourceOperations(api, logger)

        self.__logical_routes = []

    # @property
    # def _active_routes(self):
    #     if not self.__logical_routes:
    #         logical_routes = set()
    #         for routes_list in self._logical_route_operations.logical_routes_by_resource_name.values():
    #             logical_routes.update(routes_list)
    #         self.__logical_routes = list(logical_routes)
    #     return self.__logical_routes

    def _load_backup(self):
        with open(self._backup_file, 'r') as backup_file:
            data = yaml.load(backup_file)
            return data

    def initialize_resources(self, resources_arguments):
        requested_resources = self._parse_arguments(resources_arguments)
        backup_resources = self._load_backup()
        requested_backup_resources = []
        if requested_resources:
            for resource in requested_resources:
                if resource not in backup_resources:
                    raise MigrationToolException('Requested resource {} is not in the backup file'.format(resource))
                requested_backup_resources.append(backup_resources[backup_resources.index(resource)])
        else:
            requested_backup_resources = backup_resources
        return requested_backup_resources

    def define_actions(self, requested_backup_resources, connections, routes, override):
        if not connections and not routes:
            routes = connections = True
        actions_container = ActionsContainer()
        if routes:
            actions_container.update(self._route_actions(requested_backup_resources, override))
        if connections:
            actions_container.update(self._connection_actions(requested_backup_resources, override))
        return actions_container

    def _route_actions(self, requested_backup_resources, override):
        actions_container = ActionsContainer()
        for resource in requested_backup_resources:
            actions_container.update(self._route_actions_for_resource(resource, override))
        return actions_container

    def _connection_actions(self, requested_backup_resources, override):
        actions_container = ActionsContainer()
        for backup_resource in requested_backup_resources:
            cs_resource = copy(backup_resource)
            self._resource_operations.update_details(cs_resource)
            # self._logical_route_operations.get_logical_routes_table(cs_resource)
            actions_container.update(self._connection_actions_for_resource(backup_resource, cs_resource, override))
        return actions_container

    def _route_actions_for_resource(self, backup_resource, override):
        """
        :type backup_resource: cloudshell.layer_one.migration_tool.entities.Resource
        :type override: bool
        """
        create_route_actions = set()
        remove_route_actions = set()
        for route in backup_resource.associated_logical_routes:
            src_related_route = self._logical_route_operations.logical_routes_by_segment.get(route.source)
            dst_related_route = self._logical_route_operations.logical_routes_by_segment.get(route.target)
            if not src_related_route and not dst_related_route:
                create_route_actions.add(CreateRouteAction(route, self._logical_route_operations, self._logger))
            elif override:
                if src_related_route:
                    remove_route_actions.add(
                        RemoveRouteAction(src_related_route[0], self._logical_route_operations, self._logger))
                if dst_related_route:
                    remove_route_actions.add(
                        RemoveRouteAction(dst_related_route[0], self._logical_route_operations, self._logger))
                create_route_actions.add(CreateRouteAction(route, self._logical_route_operations, self._logger))
        return ActionsContainer(remove_route_actions, None, create_route_actions)

    def _connection_actions_for_resource(self, backup_resource, cs_resource, override):
        """
        :type backup_resource: cloudshell.layer_one.migration_tool.entities.Resource
        :type cs_resource: cloudshell.layer_one.migration_tool.entities.Resource
        :type override: bool
        """
        if len(backup_resource.ports) != len(cs_resource.ports):
            raise MigrationToolException('Resource  {} does not match'.format(backup_resource))
        remove_route_actions = set()
        update_connections_actions = set()
        create_route_actions = set()
        for backup_port, cs_port in zip(sorted(backup_resource.ports), sorted(cs_resource.ports)):
            if backup_port.connected_to and not cs_port.connected_to:
                connected_port_details = self._api.GetResourceDetails(backup_port.connected_to)
                if connected_port_details and not connected_port_details.Connections:
                    update_connections_actions.add(
                        UpdateConnectionAction(backup_port, self._resource_operations, self._logger))
            if override and backup_port.connected_to != cs_port.connected_to:
                update_connections_actions.add(
                    UpdateConnectionAction(backup_port, self._resource_operations, self._logger))
                logical_route = self._logical_route_operations.logical_routes_by_segment.get(cs_port.name)
                if logical_route:
                    remove_route_actions.add(
                        RemoveRouteAction(logical_route[0], self._logical_route_operations, self._logger))
                    create_route_actions.add(
                        CreateRouteAction(logical_route[0], self._logical_route_operations, self._logger))
        return ActionsContainer(remove_route_actions, update_connections_actions, create_route_actions)

    def _parse_arguments(self, resources_arguments):
        """
        :type resources_arguments: str
        """
        config_resources = []
        for config_unit in ArgumentParser(self._logger).parse_argument_string(resources_arguments):
            config_resources.extend(self._resource_operations.initialize(config_unit))
        return config_resources
