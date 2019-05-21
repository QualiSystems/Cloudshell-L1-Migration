import os
from abc import ABCMeta, abstractmethod


class ActionsContainer(object):
    def __init__(self, remove_routes=None, update_connections=None, create_routes=None):
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
    def __init__(self, logical_route, logical_route_operations, updated_connections, logger):
        super(CreateRouteAction, self).__init__(logical_route, logical_route_operations, logger)
        self._updated_connections = updated_connections

    def execute(self):
        self._refresh_route()
        try:
            self.logical_route_operations.create_route(self.logical_route)
        except Exception as e:
            self.logger.error('Cannot create route {}, reason {}'.format(self.logical_route, ','.join(e.args)))

    def _refresh_route(self):
        self.logical_route.source = self._updated_connections.get(self.logical_route.source, self.logical_route.source)
        self.logical_route.target = self._updated_connections.get(self.logical_route.target, self.logical_route.target)

    def to_string(self):
        return 'Create Route: {}'.format(self.logical_route)


class UpdateConnectionAction(Action):
    def __init__(self, src_port, dst_port, resource_operations, updated_connections, logger):
        """
        :type src_port: cloudshell.layer_one.migration_tool.entities.Port
        :type dst_port: cloudshell.layer_one.migration_tool.entities.Port
        :type resource_operations: cloudshell.layer_one.migration_tool.operations.resource_operations.ResourceOperations
        :type updated_connections: dict
        :type logger: cloudshell.layer_one.migration_tool.helpers.logger.Logger
        """
        super(UpdateConnectionAction, self).__init__(logger)
        self.src_port = src_port
        self.dst_port = dst_port
        self.resource_operations = resource_operations
        self.updated_connections = updated_connections

    def execute(self):
        try:
            self.logger.debug('**** Execute action update connection:')
            self.logger.debug('**** {} -> {}'.format(self.src_port.name, self.dst_port.name))
            self.dst_port.connected_to = self.updated_connections.get(self.src_port.connected_to,
                                                                      self.src_port.connected_to)
            self.resource_operations.update_connection(self.dst_port)
            self.updated_connections[self.src_port.name] = self.dst_port.name
        except Exception as e:
            self.logger.error('Cannot update port {}, reason {}'.format(self.dst_port, str(e)))

    def to_string(self):
        return 'Update Connection: {}=>{}'.format(self.dst_port.name, self.src_port.connected_to)

    @property
    def _comparable_unit(self):
        return ''.join([self.src_port.name, self.src_port.connected_to or ''])

    def __hash__(self):
        return hash(self._comparable_unit)

    def __eq__(self, other):
        """
        :type other: UpdateConnectionAction
        """
        return self._comparable_unit == other._comparable_unit


class CreateResourceAction(Action):
    def __init__(self, src_resource, dst_resource, resource_operations, logger):
        """
        :type src_resource: cloudshell.layer_one.migration_tool.entities.Port
        :type dst_resource: cloudshell.layer_one.migration_tool.entities.Port
        :type resource_operations: cloudshell.layer_one.migration_tool.operations.resource_operations.ResourceOperations
        :type logger: cloudshell.layer_one.migration_tool.helpers.logger.Logger
        """
        super(CreateResourceAction, self).__init__(logger)
        self.src_resource = src_resource
        self.dst_resource = dst_resource
        self.resource_operations = resource_operations

    def execute(self):
        pass

    def to_string(self):
        pass
