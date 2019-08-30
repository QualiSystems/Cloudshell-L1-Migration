from copy import copy

import yaml

from cloudshell.migration.exceptions import MigrationToolException
from cloudshell.migration.actions.core import ActionsContainer, CreateRouteAction, RemoveRouteAction, \
    UpdateConnectionAction, CreateConnectorAction
from cloudshell.migration.argument_parser.argument_helper import ArgumentOperations


class RestoreHandler(object):
    SEPARATOR = ','

    def __init__(self, api, logger, config_operations, backup_file, resource_operations, logical_route_operations):
        """
        :type api: cloudshell.api.cloudshell_api.CloudShellAPISession
        :type logger: cloudshell.migration.helpers.log_helper.Logger
        :type config_operations: cloudshell.migration.operations.config_operations.ConfigOperations
        :type backup_file: str
        :type resource_operations: cloudshell.migration.operations.resource.ResourceOperations
        :type logical_route_operations: cloudshell.migration.operations.route_operations.RouteConnectorOperations
        """
        self._api = api
        self._logger = logger
        self._config_operations = config_operations
        self._backup_file = backup_file

        self._route_connector_operations = logical_route_operations
        self._resource_operations = resource_operations
        self._updated_connections = {}

    def _load_backup(self):
        with open(self._backup_file, 'r') as backup_file:
            data = yaml.load(backup_file)
            return data

    def initialize_resources(self, resources_arguments):
        """
        :type resources_arguments: str
        :rtype: list
        """
        requested_resources = ArgumentOperations(self._logger,
                                                 self._resource_operations).initialize_existing_resources(
            resources_arguments)
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

    def define_actions(self, requested_backup_resources, connections, routes, connectors, override):
        if not connections and not routes and not connectors:
            routes = connections = connectors = True
        actions_container = ActionsContainer()
        if routes:
            actions_container.update(self._route_actions(requested_backup_resources, override))
        if connections:
            actions_container.update(self._connection_actions(requested_backup_resources, override))

        if connectors:
            actions_container.update(self._connector_actions(requested_backup_resources, override))

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
            # self._resource_operations.update_details(cs_resource)
            self._resource_operations.load_resource_ports(cs_resource)
            # self._logical_route_operations.get_logical_routes_table(cs_resource)
            actions_container.update(self._connection_actions_for_resource(backup_resource, cs_resource, override))
        return actions_container

    def _connector_actions(self, requested_backup_resources, override):
        actions_container = ActionsContainer()
        for backup_resource in requested_backup_resources:
            cs_resource = copy(backup_resource)
            # self._resource_operations.update_details(cs_resource)
            # self._resource_operations.load_resource_ports(cs_resource)
            # self._logical_route_operations.get_logical_routes_table(cs_resource)
            actions_container.update(self._connector_actions_for_resource(backup_resource, cs_resource, override))
        return actions_container

    def _route_actions_for_resource(self, backup_resource, override):
        """
        :type backup_resource: cloudshell.migration.entities.Resource
        :type override: bool
        """
        create_route_actions = set()
        remove_route_actions = set()
        for route in backup_resource.associated_logical_routes:
            src_related_route = self._route_connector_operations.logical_routes_by_segment.get(route.source)
            dst_related_route = self._route_connector_operations.logical_routes_by_segment.get(route.target)
            if not src_related_route and not dst_related_route:
                create_route_actions.add(
                    CreateRouteAction(route, self._route_connector_operations, self._updated_connections, self._logger))
            elif override:
                if src_related_route:
                    remove_route_actions.add(
                        RemoveRouteAction(src_related_route[0], self._route_connector_operations, self._logger))
                if dst_related_route:
                    remove_route_actions.add(
                        RemoveRouteAction(dst_related_route[0], self._route_connector_operations, self._logger))
                create_route_actions.add(
                    CreateRouteAction(route, self._route_connector_operations, self._updated_connections, self._logger))
        return ActionsContainer(remove_route_actions, None, create_route_actions)

    def _connection_actions_for_resource(self, backup_resource, cs_resource, override):
        """
        :type backup_resource: cloudshell.migration.entities.Resource
        :type cs_resource: cloudshell.migration.entities.Resource
        :type override: bool
        """
        if len(backup_resource.ports) != len(cs_resource.ports):
            raise MigrationToolException(
                'CS Resource "{}" does not match backup resource "{}"'.format(backup_resource, cs_resource))
        remove_route_actions = []
        update_connection_actions = []
        create_route_actions = []
        for backup_port, cs_port in zip(sorted(backup_resource.ports), sorted(cs_resource.ports)):
            if not override and backup_port.connected_to and not cs_port.connected_to:
                connected_port_details = self._api.GetResourceDetails(backup_port.connected_to)
                if connected_port_details and not connected_port_details.Connections:
                    update_connection_actions.append(
                        UpdateConnectionAction(backup_port, cs_port, self._resource_operations,
                                               self._updated_connections, self._logger))
            if override and backup_port.connected_to != cs_port.connected_to:
                update_connection_actions.append(
                    UpdateConnectionAction(backup_port, cs_port, self._resource_operations, self._updated_connections,
                                           self._logger))
                logical_route = self._route_connector_operations.logical_routes_by_segment.get(cs_port.name)
                if logical_route:
                    remove_route_actions.append(
                        RemoveRouteAction(logical_route[0], self._route_connector_operations, self._logger))
                    create_route_actions.append(
                        CreateRouteAction(logical_route[0], self._route_connector_operations, self._updated_connections,
                                          self._logger))
                # connected_to_logical_route = self._logical_route_operations.logical_routes_by_segment.get(backup_port.connected_to)
                # if connected_to_logical_route:
                #     remove_route_actions.append(
                #         RemoveRouteAction(connected_to_logical_route[0], self._logical_route_operations, self._logger))
                #     create_route_actions.append(
                #         CreateRouteAction(connected_to_logical_route[0], self._logical_route_operations, self._logger))

        return ActionsContainer(remove_route_actions, update_connection_actions, create_route_actions)

    def _connector_actions_for_resource(self, backup_resource, cs_resource, override):
        # remove_connector_actions = map(
        #     lambda connector: RemoveConnectorAction(connector, self._route_connector_operations, self._logger),
        #     src_resource.associated_connectors)
        create_connector_actions = map(
            lambda connector: CreateConnectorAction(connector, self._route_connector_operations,
                                                    self._updated_connections, self._logger),
            backup_resource.associated_connectors)
        return ActionsContainer(create_connectors=create_connector_actions)
