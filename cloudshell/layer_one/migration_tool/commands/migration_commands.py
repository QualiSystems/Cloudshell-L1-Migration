from copy import copy

from cloudshell.layer_one.migration_tool.actions import ActionsContainer, RemoveRouteAction, CreateRouteAction, \
    UpdateConnectionAction
from cloudshell.layer_one.migration_tool.helpers.config_helper import ConfigHelper
from cloudshell.layer_one.migration_tool.helpers.port_associator import PortAssociator
from cloudshell.layer_one.migration_tool.operations.argument_parser import ArgumentParser
from cloudshell.layer_one.migration_tool.operations.logical_route_operations import LogicalRouteOperations
from cloudshell.layer_one.migration_tool.operations.resource_operations import ResourceOperations


class MigrationCommands(object):

    def __init__(self, api, logger, configuration, dry_run):
        """
        :type api: cloudshell.api.cloudshell_api.CloudShellAPISession
        :type logger: cloudshell.layer_one.migration_tool.helpers.logger.Logger
        :type configuration: dict
        """
        self._api = api
        self._logger = logger
        self._configuration = configuration
        self._patterns_table = self._configuration.get(ConfigHelper.PATTERNS_TABLE_KEY)
        self._dri_run = dry_run
        self._resource_operations = ResourceOperations(api, logger, dry_run)
        self._logical_route_operations = LogicalRouteOperations(api, logger, dry_run)
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
            raise Exception(self.__class__.__name__,
                            'Number of DST resources cannot be more then number of SRC resources')

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
        return map(self._synchronize_resources_pair, resources_pairs)

    def _synchronize_resources_pair(self, resources_pair):
        src, dst = resources_pair
        if not dst.exist:
            if not dst.name:
                dst.name = self._configuration.get(ConfigHelper.NEW_RESOURCE_NAME_PREFIX_KEY, 'New_') + src.name
            dst.address = src.address
            dst.attributes = src.attributes

        if src.name == dst.name:
            raise Exception(self.__class__.__name__,
                            'SRC and DST resources cannot have the same name {}'.format(src.name))

        return resources_pair

    def initialize_actions(self, resources_pairs):
        actions_container = ActionsContainer()
        for pair in resources_pairs:
            self._load_resources(pair)
            actions_container.update(self._initialize_logical_route_actions(pair))
            actions_container.update(self._initialize_connection_actions(pair))
        return actions_container

    def _load_resources(self, resource_pair):
        """
        :type resource_pair: tuple
        """
        for resource in resource_pair:
            if not resource.exist:
                self._resource_operations.create_resource(resource)
                self._resource_operations.autoload_resource(resource)
            self._resource_operations.update_details(resource)
            self._logical_route_operations.define_logical_routes(resource)

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

    def _initialize_connection_actions(self, resource_pair):
        src_resource, dst_resource = resource_pair
        src_port_pattern = self._patterns_table.get('{}/{}'.format(src_resource.family, src_resource.model),
                                                    self._patterns_table.get(ConfigHelper.DEFAULT_PATTERN_KEY))
        dst_port_pattern = self._patterns_table.get('{}/{}'.format(dst_resource.family, dst_resource.model),
                                                    self._patterns_table.get(ConfigHelper.DEFAULT_PATTERN_KEY))
        port_associator = PortAssociator(dst_resource.ports, src_port_pattern, dst_port_pattern, self._logger)

        connection_actions = []
        for src_port in src_resource.ports:
            if src_port.connected_to:
                associated_dst_port = port_associator.associated_port(src_port)
                connection_actions.append(
                    UpdateConnectionAction(src_port, associated_dst_port, self._resource_operations,
                                           self._updated_connections, self._logger))
        return ActionsContainer(update_connections=connection_actions)

    # def prepare_operations(self, migration_configs):
    #     """
    #     :type migration_configs: list
    #     """
    #     migration_config_handler = MigrationConfigHandler(self._api, self._logger, self._configuration.get(
    #         ConfigHelper.NEW_RESOURCE_NAME_PREFIX_KEY))
    #     operations = migration_config_handler.define_operations_for_list(migration_configs)
    #     operation_validator = MigrationOperationValidator(self._api, self._logger)
    #     for operation in operations:
    #         self._operation_handler.prepare_operation(operation)
    #         operation_validator.validate(operation)
    #         if operation.valid:
    #             self._operation_handler.define_connections(operation)
    #     return operations

    # def perform_operations(self, operations):
    #     for operation in operations:
    #         if operation.valid:
    #             # try:
    #             self._operation_handler.perform_operation(operation)
    #             # except Exception as e:
    #             #     operation.success = False
    #             #     self._logger.error('Error: '.format(str(e)))
