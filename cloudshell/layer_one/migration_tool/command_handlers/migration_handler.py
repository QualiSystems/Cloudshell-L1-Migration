from copy import copy

from cloudshell.layer_one.migration_tool.exceptions import MigrationToolException
from cloudshell.layer_one.migration_tool.helpers.port_associator import PortAssociator
from cloudshell.layer_one.migration_tool.operational_entities.actions import ActionsContainer, RemoveRouteAction, \
    CreateRouteAction, \
    UpdateConnectionAction
from cloudshell.layer_one.migration_tool.operations.argument_parser import ArgumentParser


class MigrationHandler(object):

    def __init__(self, api, logger, config_helper, resource_operations, logical_route_operations):
        """
        :type api: cloudshell.api.cloudshell_api.CloudShellAPISession
        :type logger: cloudshell.layer_one.migration_tool.helpers.logger.Logger
        :type config_helper: cloudshell.layer_one.migration_tool.helpers.config_helper.ConfigHelper
        :type resource_operations: cloudshell.layer_one.migration_tool.operations.resource_operations.ResourceOperations
        :type logical_route_operations: cloudshell.layer_one.migration_tool.operations.logical_route_operations.LogicalRouteOperations
        """
        self._api = api
        self._logger = logger
        self._config_helper = config_helper
        self._resource_operations = resource_operations
        self._logical_route_operations = logical_route_operations
        self._updated_connections = {}

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
        return map(self._validate_resources_pair, map(self._synchronize_resources_pair, resources_pairs))

    def _synchronize_resources_pair(self, resources_pair):
        src, dst = resources_pair
        if not dst.exist:
            if not dst.name:
                dst.name = self._config_helper.read_key(self._config_helper.NEW_RESOURCE_NAME_PREFIX_KEY,
                                                        self._config_helper.DEFAULT_CONFIGURATION.get(
                                                        self._config_helper.NEW_RESOURCE_NAME_PREFIX_KEY)) + src.name
            dst.address = src.address

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

    def initialize_actions(self, resources_pairs, override):
        actions_container = ActionsContainer()
        for pair in resources_pairs:
            self._load_resources(pair)
            actions_container.update(self._initialize_logical_route_actions(pair))
            actions_container.update(self._initialize_connection_actions(pair, override))
        return actions_container

    def _load_resources(self, resource_pair):
        """
        :type resource_pair: tuple
        """
        src, dst = resource_pair

        # Load SRC resource
        if not src.ports:
            self._resource_operations.update_details(src)
            self._logical_route_operations.define_logical_routes(src)

        # Load DST resource
        dst.attributes = src.attributes
        if not dst.exist:
            self._resource_operations.create_resource(dst)
            self._resource_operations.autoload_resource(dst)
        # else:
        #     self._resource_operations.sync_from_device(dst)

        if not dst.ports:
            self._resource_operations.update_details(dst)
            self._logical_route_operations.define_logical_routes(dst)

    def _initialize_logical_route_actions(self, resource_pair):
        actions_container = ActionsContainer()
        for resource in resource_pair:
            remove_route_actions = map(
                lambda logical_route: RemoveRouteAction(logical_route, self._logical_route_operations, self._logger),
                resource.associated_logical_routes)
            create_route_actions = map(
                lambda logical_route: CreateRouteAction(logical_route, self._logical_route_operations, self._logger),
                resource.associated_logical_routes)
            actions_container.update(
                ActionsContainer(remove_routes=remove_route_actions, create_routes=create_route_actions))
        return actions_container

    def _initialize_connection_actions(self, resource_pair, override):
        src_resource, dst_resource = resource_pair
        port_associator = PortAssociator(src_resource, dst_resource, self._config_helper, self._logger)

        connection_actions = []

        for src_port, dst_port in port_associator.associated_pairs():
            if override or not dst_port.connected_to:
                connection_actions.append(
                    UpdateConnectionAction(src_port, dst_port, self._resource_operations,
                                           self._updated_connections, self._logger))
        return ActionsContainer(update_connections=connection_actions)
