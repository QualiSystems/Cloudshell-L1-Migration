from collections import defaultdict
from copy import copy

from cloudshell.migration.actions.blueprint import UpdateBlueprintAction
from cloudshell.migration.actions.connection import UpdateConnectionAction
from cloudshell.migration.actions.connector import UpdateConnectorAction
from cloudshell.migration.actions.core import ActionsContainer
from cloudshell.migration.actions.logical_route import UpdateL1RouteAction, UpdateRouteAction
from cloudshell.migration.associations.port_associator import PortAssociator
from cloudshell.migration.exceptions import MigrationToolException
from cloudshell.migration.helpers.argument_helper import ArgumentParser


class BasicInitializationFlow(object):
    def __init__(self, logger, configuration, resource_operations, route_operations, connector_operations):
        """
        :type logger: logging.Logger
        :type configuration: cloudshell.migration.config.Configuration
        :type resource_operations: cloudshell.migration.operations.resource_operations.ResourceOperations
        :type route_operations: cloudshell.migration.operations.route_operations.RouteOperations
        :type connector_operations: cloudshell.migration.operations.connector_operations.ConnectorOperations
        """
        self._logger = logger
        self._configuration = configuration
        self._resource_operations = resource_operations
        self._route_operations = route_operations
        self._connector_operations = connector_operations

    def define_resources_pairs(self, src_resources_arguments, dst_resources_arguments):
        argument_parser = ArgumentParser(self._logger, self._resource_operations)
        src_resources = argument_parser.initialize_existing_resources(src_resources_arguments)
        dst_resources = argument_parser.initialize_resources_with_stubs(dst_resources_arguments)
        return self._initialize_resources_pairs(src_resources, dst_resources)

    def _initialize_resources_pairs(self, src_resources, dst_resources):
        """
        :type src_resources: list
        :type dst_resources: list
        """

        if len(src_resources) < len(dst_resources):
            raise MigrationToolException('Number of DST resources cannot be more then number of SRC resources')

        resources_pairs = []
        for index in xrange(len(src_resources)):
            src = src_resources[index]
            if index < len(dst_resources):
                dst = dst_resources[index]
            else:
                dst = copy(dst_resources[-1])
                dst_resources.append(dst)
            pair = src, dst
            resources_pairs.append(pair)

        for pair in resources_pairs:
            self._synchronize_resources_pair(pair)
            self._validate_resources_pair(pair)
            self._load_resources_pair(pair)

        return resources_pairs

    def _synchronize_resources_pair(self, resources_pair):
        src, dst = resources_pair

        # Create DST if not exist
        if not dst.exist:
            self._resource_operations.update_details(src)
            if not dst.name:
                dst.name = self._configuration.resource_name_prefix + src.name
            dst.address = src.address
            self._resource_operations.create_resource(dst)

            # Sync attributes
            self._resource_operations.load_resource_attributes(src)
            self._resource_operations.load_resource_attributes(dst)
            for name, src_attr in src.attributes.items():
                dst_attr = dst.attributes.get(name)
                if dst_attr:
                    dst_attr.Value = src_attr.Value
                    self._logger.debug("Sync attribute value: {} -> {}".format(src_attr.Name, dst_attr.Name))
                else:
                    self._logger.debug("Cannot find attribute name {} for src attr {}".format(name, src_attr.Name))
            self._resource_operations.set_resource_attributes(dst)

        return resources_pair

    def _validate_resources_pair(self, resources_pair, handled_resources=[]):
        """
        :param tuple resources_pair:
        :param list handled_resources:
        :return:
        """
        src, dst = resources_pair

        if src.name == dst.name:
            raise MigrationToolException('SRC and DST resources cannot have the same name {}'.format(src.name))
        if not src.exist:
            raise MigrationToolException('SRC resource {} does not exist'.format(src.name))

        if not dst.exist:
            if dst.name in [resource.name for resource in
                            self._resource_operations.sorted_by_family_model_resources.get((dst.family, dst.model),
                                                                                           [])]:
                raise MigrationToolException('Resource with name {} already exist'.format(dst.name))
        for resource in resources_pair:
            if resource.name in handled_resources:
                raise MigrationToolException(
                    'Resource with name {} already used in another migration pair'.format(resource.name))
            else:
                handled_resources.append(resource.name)
        return resources_pair

    def _load_resources_pair(self, resource_pair):
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
            self._resource_operations.sync_from_device(dst)
            # pass

        for resource in resource_pair:
            if not resource.ports:
                self._resource_operations.load_resource_ports(resource)
        return resource_pair


class ActionsInitializationFlow(object):

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

    def initialize_actions(self, resources_pairs, override):
        container = ActionsContainer()
        for pair in resources_pairs:
            src_resource, dst_resource = pair
            port_associator = PortAssociator(src_resource, dst_resource, self._configuration, self._logger)
            if not port_associator.valid():
                raise MigrationToolException('Cannot associate {} to {}'.format(src_resource, dst_resource))
            self._associations_table.update(port_associator.associations_table())
            container.append(self._initialize_connection_actions(port_associator, override))
            container.append(self._initialize_logical_route_actions(pair))
            container.append(self._initialize_connector_actions(pair, override))
            container.append(self._initialize_blueprint_actions(pair))

        return container

    def _initialize_connection_actions(self, port_associator, override):
        # src_resource, dst_resource = resource_pair
        # port_associator = PortAssociator(src_resource, dst_resource, self._configuration, self._logger)

        connection_actions = []

        for src_port, dst_port in port_associator.associated_connected_pairs():
            if override or not dst_port.connected_to:
                connection_actions.append(
                    UpdateConnectionAction(src_port, dst_port, self._resource_operations,
                                           self._updated_connections, self._logger))
        return connection_actions

    def _initialize_logical_route_actions(self, resource_pair):
        src_resource = resource_pair[0]

        if self._resource_operations.is_l1_resource(src_resource):
            self._route_operations.load_segment_logical_routes(src_resource)
        else:
            self._route_operations.load_endpoint_logical_routes(src_resource)

        action_type = UpdateL1RouteAction if src_resource.l1_resource else UpdateRouteAction
        update_route_actions = map(
            lambda logical_route: action_type(logical_route, self._route_operations,
                                              self._updated_connections, self._logger),
            src_resource.associated_logical_routes)
        return update_route_actions

    def _initialize_connector_actions(self, resource_pair, override):
        src_resource = resource_pair[0]
        """
        :type src_resource: cloudshell.migration.entities.Resource
        """
        if not self._resource_operations.is_l1_resource(src_resource):
            self._connector_operations.load_connectors(src_resource)

        actions = map(
            lambda connector: UpdateConnectorAction(connector, self._connector_operations,
                                                    self._associations_table, self._logger),
            src_resource.associated_connectors)
        return actions

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
        return actions
