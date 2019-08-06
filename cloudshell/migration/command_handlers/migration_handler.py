from collections import defaultdict
from copy import copy

from cloudshell.migration.exceptions import MigrationToolException
from cloudshell.migration.associations.port_associator import PortAssociator
from cloudshell.migration.actions.core import ActionsContainer, \
    UpdateConnectionAction, UpdateBlueprintAction, UpdateRouteAction, \
    UpdateConnectorAction, UpdateL1RouteAction
from cloudshell.migration.helpers.argument_helper import ArgumentOperations


class MigrationHandler(object):

    def __init__(self, logger, configuration, resource_operations, connection_operations, route_operations,
                 connector_operations, topologies_operations, package_operations):
        """
        :type logger: logging.Logger
        :type configuration: cloudshell.migration.config.Configuration
        :type resource_operations: cloudshell.migration.operations.resource_operations.ResourceOperations
        :type connection_operations: loudshell.migration.operations.connection_operations.ConnectionOperations
        :type route_operations: cloudshell.migration.operations.route_operations.RouteOperations
        :type connector_operations: cloudshell.migration.operations.connector_operations.ConnectorOperations
        :type topologies_operations: cloudshell.migration.operations.blueprint_operations.TopologiesOperations
        :type package_operations: cloudshell.migration.operations.blueprint_operations.PackageOperations
        """
        self._logger = logger
        self._configuration = configuration
        self._resource_operations = resource_operations
        self._connection_operations = connection_operations
        self._route_operations = route_operations
        self._connector_operations = connector_operations
        self._topologies_operations = topologies_operations
        self._package_operations = package_operations
        self._updated_connections = {}
        self._associations_table = {}

    @classmethod
    def from_factory(cls, factory):
        """
        :param cloudshell.migration.factory.Factory factory:
        :return:
        """
        return cls(factory.logger, factory.configuration, factory.resource_operations, factory.connection_operations,
                   factory.route_operations, factory.connector_operations, factory.topologies_operations,
                   factory.package_operations)

    def _load_resources(self, resource_pair):
        """
        :type resource_pair: tuple
        """
        src, dst = resource_pair

        # # Load SRC resource
        # if not src.ports:
        #     self._resource_operations.load_resource_ports(src)
        #     self._logical_route_operations.load_logical_routes(src)

        # Load DST resource
        if not dst.exist:
            self._resource_operations.autoload_resource(dst)
        else:
            # self._resource_operations.sync_from_device(dst)
            pass

        for resource in resource_pair:
            if not resource.ports:
                self._resource_operations.load_resource_ports(resource)

        if self._resource_operations.is_l1_resource(src):
            self._route_operations.load_segment_logical_routes(src)
        else:
            self._route_operations.load_endpoint_logical_routes(src)
            self._connector_operations.load_connectors(src)

    def initialize_actions(self, resources_pairs, override):
        actions_container = ActionsContainer()
        for pair in resources_pairs:
            src_resource, dst_resource = pair
            self._load_resources(pair)
            port_associator = PortAssociator(src_resource, dst_resource, self._configuration, self._logger)
            self._associations_table.update(port_associator.association_table())
            actions_container.update(self._initialize_connection_actions(port_associator, override))
            actions_container.update(self._initialize_logical_route_actions(pair))
            actions_container.update(self._initialize_connector_actions(pair, override))
            actions_container.update(self._initialize_blueprint_actions(pair))

        return actions_container

    def _initialize_logical_route_actions(self, resource_pair):
        src_resource = resource_pair[0]

        action_class = UpdateL1RouteAction if src_resource.l1_resource else UpdateRouteAction
        update_route_actions = map(
            lambda logical_route: action_class(logical_route, self._route_operations,
                                               self._updated_connections, self._logger),
            src_resource.associated_logical_routes)
        return ActionsContainer(update_routes=update_route_actions)

    def _initialize_connection_actions(self, port_associator, override):
        # src_resource, dst_resource = resource_pair
        # port_associator = PortAssociator(src_resource, dst_resource, self._configuration, self._logger)

        connection_actions = []

        for src_port, dst_port in port_associator.associated_connected_pairs():
            if override or not dst_port.connected_to:
                connection_actions.append(
                    UpdateConnectionAction(src_port, dst_port, self._resource_operations,
                                           self._updated_connections, self._logger))
        return ActionsContainer(update_connections=connection_actions)

    def _initialize_connector_actions(self, resource_pair, override):
        src_resource = resource_pair[0]
        """
        :type src_resource: cloudshell.migration.entities.Resource
        """
        # remove_connector_actions = map(
        #     lambda connector: RemoveConnectorAction(connector, self._route_connector_operations, self._logger),
        #     src_resource.associated_connectors)
        # create_connector_actions = map(
        #     lambda connector: CreateConnectorAction(connector, self._route_connector_operations,
        #                                             self._associations_table, self._logger),
        #     src_resource.associated_connectors)
        update_connector_actions = map(
            lambda connector: UpdateConnectorAction(connector, self._connector_operations,
                                                    self._associations_table, self._logger),
            src_resource.associated_connectors)
        return ActionsContainer(update_connectors=update_connector_actions)

    def _initialize_blueprint_actions(self, resource_pair):
        src_resource = resource_pair[0]
        """
        :type src_resource: cloudshell.migration.entities.Resource
        """
        routes, connectors = self._topologies_operations.logical_routes_connectors_by_resource_name.get(
            src_resource.name, ([], []))
        blueprint_table = defaultdict(lambda: ([], []))
        for route in routes:
            blueprint_table[route.blueprint][0].append(route)

        for connector in connectors:
            blueprint_table[connector.blueprint][1].append(connector)

        actions = []
        for blueprint_name, data in blueprint_table.items():
            actions.append(
                UpdateBlueprintAction(blueprint_name, data[0], data[1], self.quali_api, self._associations_table,
                                      self._logger))
        return ActionsContainer(update_blueprint=actions)
