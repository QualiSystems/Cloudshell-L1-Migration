from abc import ABCMeta, abstractmethod


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


class RemoveRouteAction(Action):

    def __init__(self, logical_route, logical_route_operations, logger):
        """
        :type logical_route:  cloudshell.layer_one.migration_tool.entities.LogicalRoute
        :type logical_route_operations: cloudshell.layer_one.migration_tool.operations.logical_route_operations.LogicalRouteOperations
        """
        super(RemoveRouteAction, self).__init__(logger)
        self.logical_route = logical_route
        self.logical_route_operations = logical_route_operations

    def execute(self):
        try:
            self.logical_route_operations.remove_route(self.logical_route)
        except Exception as e:
            self.logger.error('Cannot remove route {}, reason {}'.format(self.logical_route, ','.join(e.args)))

    def to_string(self):
        return 'Remove Route: {}'.format(self.logical_route)

    def __str__(self):
        return self.to_string()


class CreateRouteAction(Action):

    def __init__(self, logical_route, logical_route_operations, logger):
        """
        :type logical_route:  cloudshell.layer_one.migration_tool.entities.LogicalRoute
        :type logical_route_operations: cloudshell.layer_one.migration_tool.operations.logical_route_operations.LogicalRouteOperations
        """
        super(CreateRouteAction, self).__init__(logger)
        self.logical_route = logical_route
        self.logical_route_operations = logical_route_operations

    def execute(self):
        try:
            self.logical_route_operations.create_route(self.logical_route)
        except Exception as e:
            self.logger.error('Cannot create route {}, reason {}'.format(self.logical_route, ','.join(e.args)))

    def to_string(self):
        return 'Create Route: {}'.format(self.logical_route)

    def __str__(self):
        return self.to_string()


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
            self.logger.error('Cannot update port {}, reason {}'.format(self.port, ','.join(e.args)))

    def to_string(self):
        return 'Update Connection: {}'.format(self.port)

    def __str__(self):
        return self.to_string()
