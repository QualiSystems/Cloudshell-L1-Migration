import os
from abc import ABCMeta, abstractmethod


class ActionsContainer(object):
    def __init__(self, remove_routes=None, update_connections=None, create_routes=None):
        # self.resource = resource
        self.remove_routes = remove_routes or []
        self.update_connections = update_connections or []
        self.create_routes = create_routes or []

    def sequence(self):
        sequence = []
        sequence.extend(set(self.remove_routes))
        sequence.extend(set(self.update_connections))
        sequence.extend(set(self.create_routes))
        return sequence

    def execute_actions(self):
        return map(lambda x: x.execute(), self.sequence())

    def update(self, container):
        """
        :type container: ActionsContainer
        """
        self.remove_routes = set(self.remove_routes) | set(container.remove_routes)
        self.update_connections = set(self.update_connections) | set(container.update_connections)
        self.create_routes = set(self.create_routes) | set(container.create_routes)

    def to_string(self):
        out = ''
        for action in self.sequence():
            out += action.to_string() + os.linesep
        return out

    def is_empty(self):
        return False if self.remove_routes or self.update_connections or self.create_routes else True

    def __str__(self):
        return self.to_string()


class Action(object):
    __metaclass__ = ABCMeta

    def __init__(self, logger):
        """
        :type logger: cloudshell.layer_one.migration_tool.helpers.logger.Logger
        """
        self.logger = logger

    @abstractmethod
    def execute(self):
        pass

    @abstractmethod
    def to_string(self):
        pass

    def __str__(self):
        return self.to_string()


class LogicalRouteAction(Action):
    __metaclass__ = ABCMeta

    def __init__(self, logical_route, logical_route_operations, logger):
        """
        :type logical_route:  cloudshell.layer_one.migration_tool.entities.LogicalRoute
        :type logical_route_operations: cloudshell.layer_one.migration_tool.operations.logical_route_operations.LogicalRouteOperations
        """
        super(LogicalRouteAction, self).__init__(logger)
        self.logical_route = logical_route
        self.logical_route_operations = logical_route_operations

    def __hash__(self):
        return hash(self.logical_route)

    def __eq__(self, other):
        return self.logical_route == other.logical_route


class RemoveRouteAction(LogicalRouteAction):

    def execute(self):
        try:
            self.logical_route_operations.remove_route(self.logical_route)
        except Exception as e:
            self.logger.error('Cannot remove route {}, reason {}'.format(self.logical_route, ','.join(e.args)))

    def to_string(self):
        return 'Remove Route: {}'.format(self.logical_route)


class CreateRouteAction(LogicalRouteAction):
    def execute(self):
        try:
            self.logical_route_operations.create_route(self.logical_route)
        except Exception as e:
            self.logger.error('Cannot create route {}, reason {}'.format(self.logical_route, ','.join(e.args)))

    def to_string(self):
        return 'Create Route: {}'.format(self.logical_route)


class UpdateConnectionAction(Action):
    def __init__(self, port, resource_operations, logger):
        """
        :type port: cloudshell.layer_one.migration_tool.entities.Port
        :type resource_operations: cloudshell.layer_one.migration_tool.operations.resource_operations.ResourceOperations
        """
        super(UpdateConnectionAction, self).__init__(logger)
        self.port = port
        self.resource_operations = resource_operations

    def execute(self):
        try:
            self.resource_operations.update_connection(self.port)
        except Exception as e:
            self.logger.error('Cannot update port {}, reason {}'.format(self.port, str(e)))

    def to_string(self):
        return 'Update Connection: {}'.format(self.port)

    def __hash__(self):
        return hash(''.join(sorted([self.port.name, self.port.connected_to])))

    def __eq__(self, other):
        return sorted([self.port.name, self.port.connected_to]) == sorted([other.port.name, other.port.connected_to])
