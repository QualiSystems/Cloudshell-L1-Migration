from collections import defaultdict
from copy import copy

from cloudshell.migration.exceptions import MigrationToolException
from cloudshell.migration.helpers.port_associator import PortAssociator
from cloudshell.migration.operational_entities.actions import ActionsContainer, \
    UpdateConnectionAction, UpdateBlueprintAction, UpdateRouteAction, \
    UpdateConnectorAction, UpdateL1RouteAction
from cloudshell.migration.operations.argument_operations import ArgumentOperations


class MigrationHandler(object):

    def __init__(self, api, logger, config_operations, resource_operations, logical_route_operations,
                 topologies_operations, quali_api):
        """
        :type api: cloudshell.api.cloudshell_api.CloudShellAPISession
        :type logger: logging.Logger
        :type config_operations: cloudshell.migration.operations.config_operations.ConfigOperations
        :type resource_operations: cloudshell.migration.operations.resource_operations.ResourceOperations
        :type logical_route_operations: cloudshell.migration.operations.route_connector_operations.RouteConnectorOperations
        :type topologies_operations: cloudshell.migration.operations.blueprint_operations.TopologiesOperations
        :type quali_api: cloudshell.migration.libs.quali_api.QualiAPISession
        """
        self._api = api
        self._logger = logger
        self._config_operations = config_operations
        self._resource_operations = resource_operations
        self._route_connector_operations = logical_route_operations
        self._topologies_operations = topologies_operations
        self.quali_api = quali_api
        self._updated_connections = {}
        self._associations_table = {}

    def define_resources_pairs(self, src_resources_arguments, dst_resources_arguments):
        argument_parser = ArgumentOperations(self._logger, self._resource_operations)
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
        return map(self._validate_resources_pair, map(self._synchronize_resources_pair, resources_pairs))

    def _synchronize_resources_pair(self, resources_pair):
        src, dst = resources_pair

        # Create DST if not exist
        if not dst.exist:
            self._resource_operations.update_details(src)
            if not dst.name:
                dst.name = self._config_operations.read_key_or_default(
                    self._config_operations.KEY.NEW_RESOURCE_NAME_PREFIX) + src.name
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
            self._resource_operations.sync_from_device(dst)
            # pass

        for resource in resource_pair:
            if not resource.ports:
                self._resource_operations.load_resource_ports(resource)

        if src.l1_resource():
            self._route_connector_operations.load_segment_logical_routes(src)
        else:
            self._route_connector_operations.load_endpoint_logical_routes(src)
            self._route_connector_operations.load_connectors(src)

    def initialize_actions(self, resources_pairs, override):
        actions_container = ActionsContainer()
        for pair in resources_pairs:
            src_resource, dst_resource = pair
            self._load_resources(pair)
            port_associator = PortAssociator(src_resource, dst_resource, self._config_operations, self._logger)
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
            lambda logical_route: action_class(logical_route, self._route_connector_operations,
                                               self._updated_connections, self._logger),
            src_resource.associated_logical_routes)
        return ActionsContainer(update_routes=update_route_actions)

    def _initialize_connection_actions(self, port_associator, override):
        # src_resource, dst_resource = resource_pair
        # port_associator = PortAssociator(src_resource, dst_resource, self._config_operations, self._logger)

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
            lambda connector: UpdateConnectorAction(connector, self._route_connector_operations,
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
