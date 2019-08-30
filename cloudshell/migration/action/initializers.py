from collections import defaultdict

from cloudshell.migration.action.blueprint import UpdateBlueprintAction
from cloudshell.migration.action.connection import UpdateConnectionAction
from cloudshell.migration.action.connector import UpdateConnectorAction
from cloudshell.migration.action.core import Initializer, ActionsContainer
from cloudshell.migration.action.logical_route import UpdateL1RouteAction, UpdateRouteAction


class ConnectionInitializer(Initializer):

    def initialize(self, resource_pair, override):
        association = self._associator.get_association(resource_pair)

        connection_actions = []

        for src_port, dst_port in association.iter_pairs():
            if override or not dst_port.connected_to:
                connection_actions.append(
                    UpdateConnectionAction(src_port, dst_port, self._operations_factory.connection_operations,
                                           self._associator.updated_connections, self._logger))
        return ActionsContainer(connection_actions)


class L1RouteInitializer(Initializer):

    def initialize(self, resource_pair, override):
        route_operations = self._operations_factory.route_operations
        src_resource = resource_pair.src_resource

        if route_operations.is_l1_resource(src_resource):
            route_operations.load_segment_logical_routes(src_resource)

        route_actions = map(
            lambda logical_route: UpdateL1RouteAction(logical_route, route_operations,
                                                      self._associator.updated_connections, self._logger),
            src_resource.associated_logical_routes)

        return ActionsContainer(route_actions)


class RouteInitializer(Initializer):

    def initialize(self, resource_pair, override):
        route_operations = self._operations_factory.route_operations
        src_resource = resource_pair.src_resource

        if not route_operations.is_l1_resource(src_resource):
            route_operations.load_endpoint_logical_routes(src_resource)

        route_actions = map(
            lambda logical_route: UpdateRouteAction(logical_route, route_operations,
                                                    self._associator.updated_connections, self._logger),
            src_resource.associated_logical_routes)

        return ActionsContainer(route_actions)


class ConnectorInitializer(Initializer):

    def initialize(self, resource_pair, override):
        src_resource = resource_pair.src_resource
        connector_operations = self._operations_factory.connector_operations

        if not connector_operations.is_l1_resource(src_resource):
            connector_operations.load_connectors(src_resource)

        actions = map(
            lambda connector: UpdateConnectorAction(connector, connector_operations,
                                                    self._associator.associations_table, self._logger),
            src_resource.associated_connectors)
        return ActionsContainer(actions)


class BlueprintInitializer(Initializer):

    def initialize(self, resource_pair, override):
        src_resource = resource_pair.src_resource
        topologies_operations = self._operations_factory.topologies_operations
        routes, connectors = topologies_operations.logical_routes_connectors_by_resource_name.get(
            src_resource.name, ([], []))
        blueprint_table = defaultdict(lambda: ([], []))
        for route in routes:
            blueprint_table[route.blueprint][0].append(route)

        for connector in connectors:
            blueprint_table[connector.blueprint][1].append(connector)

        actions = []
        for blueprint_name, data in blueprint_table.items():
            actions.append(
                UpdateBlueprintAction(blueprint_name, data[0], data[1], self._operations_factory.package_operations,
                                      self._associator.associations_table,
                                      self._logger))
        return ActionsContainer(actions)

# class ActionsInitialization(object):
#
#     def __init__(self, logger, configuration, resource_operations, connection_operations, route_operations,
#                  connector_operations, topologies_operations, package_operations):
#         """
#         :type logger: logging.Logger
#         :type configuration: cloudshell.migration.config.Configuration
#         :type resource_operations: cloudshell.migration.operations.resource.ResourceOperations
#         :type connection_operations: loudshell.migration.operations.connection_operations.ConnectionOperations
#         :type route_operations: cloudshell.migration.operations.route.RouteOperations
#         :type connector_operations: cloudshell.migration.operations.connector.ConnectorOperations
#         :type topologies_operations: cloudshell.migration.operations.blueprint_operations.TopologiesOperations
#         :type package_operations: cloudshell.migration.operations.blueprint_operations.PackageOperations
#         """
#         self._logger = logger
#         self._configuration = configuration
#         self._resource_operations = resource_operations
#         self._connection_operations = connection_operations
#         self._route_operations = route_operations
#         self._connector_operations = connector_operations
#         self._topologies_operations = topologies_operations
#         self._package_operations = package_operations
#         self._updated_connections = {}
#         self._associations_table = {}
#
#     @classmethod
#     def from_factory(cls, factory):
#         """
#         :param cloudshell.migration.factory.Factory factory:
#         :return:
#         """
#         return cls(factory.logger, factory.configuration, factory.resource_operations, factory.connection_operations,
#                    factory.route_operations, factory.connector_operations, factory.topologies_operations,
#                    factory.package_operations)
#
#     def initialize_actions(self, resources_pairs, override):
#         container = ActionsContainer()
#         for pair in resources_pairs:
#             src_resource, dst_resource = pair
#             port_associator = PortAssociator(src_resource, dst_resource, self._configuration, self._logger)
#             if not port_associator.valid():
#                 raise MigrationToolException('Cannot associate {} to {}'.format(src_resource, dst_resource))
#             self._associations_table.update(port_associator.associations_table())
#             container.append(self._initialize_connection_actions(port_associator, override))
#             container.append(self._initialize_logical_route_actions(pair))
#             container.append(self._initialize_connector_actions(pair, override))
#             container.append(self._initialize_blueprint_actions(pair))
#
#         return container
#
#     def initialize_connection_actions(self, resource_pair, override):
#         # src_resource, dst_resource = resource_pair
#         # port_associator = PortAssociator(src_resource, dst_resource, self._configuration, self._logger)
#
#         connection_actions = []
#
#         for src_port, dst_port in port_associator.associated_connected_pairs():
#             if override or not dst_port.connected_to:
#                 connection_actions.append(
#                     UpdateConnectionAction(src_port, dst_port, self._resource_operations,
#                                            self._updated_connections, self._logger))
#         return connection_actions
#
#     def initialize_logical_route_actions(self, resource_pair):
#         src_resource = resource_pair[0]
#
#         if self._resource_operations.is_l1_resource(src_resource):
#             self._route_operations.load_segment_logical_routes(src_resource)
#         else:
#             self._route_operations.load_endpoint_logical_routes(src_resource)
#
#         action_type = UpdateL1RouteAction if src_resource.l1_resource else UpdateRouteAction
#         update_route_actions = map(
#             lambda logical_route: action_type(logical_route, self._route_operations,
#                                               self._updated_connections, self._logger),
#             src_resource.associated_logical_routes)
#         return update_route_actions
#
#     def initialize_connector_actions(self, resource_pair, override):
#         src_resource = resource_pair[0]
#         """
#         :type src_resource: cloudshell.migration.entities.Resource
#         """
#         if not self._resource_operations.is_l1_resource(src_resource):
#             self._connector_operations.load_connectors(src_resource)
#
#         actions = map(
#             lambda connector: UpdateConnectorAction(connector, self._connector_operations,
#                                                     self._associations_table, self._logger),
#             src_resource.associated_connectors)
#         return actions
#
#     def initialize_blueprint_actions(self, resource_pair):
#         src_resource = resource_pair[0]
#         """
#         :type src_resource: cloudshell.migration.entities.Resource
#         """
#         routes, connectors = self._topologies_operations.logical_routes_connectors_by_resource_name.get(
#             src_resource.name, ([], []))
#         blueprint_table = defaultdict(lambda: ([], []))
#         for route in routes:
#             blueprint_table[route.blueprint][0].append(route)
#
#         for connector in connectors:
#             blueprint_table[connector.blueprint][1].append(connector)
#
#         actions = []
#         for blueprint_name, data in blueprint_table.items():
#             actions.append(
#                 UpdateBlueprintAction(blueprint_name, data[0], data[1], self.quali_api, self._associations_table,
#                                       self._logger))
#         return actions
