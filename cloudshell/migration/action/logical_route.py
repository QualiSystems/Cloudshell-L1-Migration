from abc import ABCMeta
from copy import deepcopy

from backports.functools_lru_cache import lru_cache

from cloudshell.migration.action.core import Action, ActionsContainer


class LogicalRouteAction(Action):
    __metaclass__ = ABCMeta
    priority = Action._EXECUTION_STAGE.TWO

    def __init__(self, logical_route, logical_route_operations, updated_connections, logger):
        """
        :type logical_route:  cloudshell.migration.core.model.entities.LogicalRoute
        :type logical_route_operations: cloudshell.migration.core.operations.route.RouteOperations
        :type updated_connections: dict
        :type logger: logging.Logger
        """
        super(LogicalRouteAction, self).__init__(logger)
        self.logical_route = logical_route
        self.logical_route_operations = logical_route_operations
        self._updated_connections = updated_connections

    @property
    @lru_cache()
    def _updated_route(self):
        fresh_route = deepcopy(self.logical_route)
        fresh_route.source = self._updated_connections.get(self.logical_route.source, self.logical_route.source)
        fresh_route.target = self._updated_connections.get(self.logical_route.target, self.logical_route.target)
        for port in fresh_route.associated_ports:
            port.name = self._updated_connections.get(port.name, port.name)
        return fresh_route

    def __hash__(self):
        return hash(self.logical_route)

    def __eq__(self, other):
        return Action.__eq__(self, other) and self.logical_route == other.logical_route

    def description(self):
        return '{} {}'.format(self.ACTION_DESCR, self.logical_route)


class UpdateL1RouteAction(LogicalRouteAction):
    ACTION_DESCR = 'Update L1 Route'

    def execute(self):
        for port in self._updated_route.associated_ports:
            self._logger.debug(
                'Adding {} to reservation id {}'.format(port.name, self._updated_route.reservation_id))
            self.logical_route_operations.add_to_reservation(self._updated_route.reservation_id, port.name)

    @staticmethod
    def initialize_for_pair(resource_pair, override, associations_table, operations_factory, logger):
        route_operations = operations_factory.route_operations
        src_resource = resource_pair.src_resource

        if route_operations.is_l1_resource(src_resource):
            route_operations.load_segment_logical_routes(src_resource)

            route_actions = map(
                lambda logical_route: UpdateL1RouteAction(logical_route, route_operations,
                                                          resource_pair.updated_connections, logger),
                src_resource.associated_logical_routes)
        else:
            route_actions = []

        return ActionsContainer(route_actions)


class UpdateRouteAction(LogicalRouteAction):
    ACTION_DESCR = 'Update Route'

    def execute(self):
        self._logger.debug("Creating route {}".format(self._updated_route))
        self.logical_route_operations.create_route(self._updated_route)
        self._logger.debug("Removing route {}".format(self.logical_route))
        self.logical_route_operations.remove_route(self.logical_route)

    @staticmethod
    def initialize_for_pair(resource_pair, override, associations_table, operations_factory, logger):
        route_operations = operations_factory.route_operations
        src_resource = resource_pair.src_resource

        if not route_operations.is_l1_resource(src_resource):
            route_operations.load_endpoint_logical_routes(src_resource)

            route_actions = map(
                lambda logical_route: UpdateRouteAction(logical_route, route_operations,
                                                        resource_pair.updated_connections, logger),
                src_resource.associated_logical_routes)
        else:
            route_actions = []

        return ActionsContainer(route_actions)
