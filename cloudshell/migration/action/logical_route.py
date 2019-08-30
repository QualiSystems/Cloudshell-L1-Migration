from abc import ABCMeta

from cloudshell.migration.action.core import Action


class LogicalRouteAction(Action):
    __metaclass__ = ABCMeta
    priority = Action.EXECUTION_PRIORITY.MIDDLE

    def __init__(self, logical_route, logical_route_operations, logger):
        """
        :type logical_route:  cloudshell.migration.entities.LogicalRoute
        :type logical_route_operations: cloudshell.migration.operations.route_operations.RouteConnectorOperations
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
            return self.to_string() + " ... Done"
        except Exception as e:
            self.logger.error('Cannot remove route {}, reason {}'.format(self.logical_route, ','.join(e.args)))
            return self.to_string() + "... Failed"

    def to_string(self):
        return 'Remove Route: {}'.format(self.logical_route)


class CreateRouteAction(LogicalRouteAction):
    def __init__(self, logical_route, logical_route_operations, updated_connections, logger):
        super(CreateRouteAction, self).__init__(logical_route, logical_route_operations, logger)
        self._updated_connections = updated_connections

    def execute(self):
        self._refresh_route()
        self.logger.debug('Create Logical Route {}'.format(self.logical_route))
        try:
            self.logical_route_operations.create_route(self.logical_route)
            return self.to_string() + " ... Done"
        except Exception as e:
            self.logger.error('Cannot create route {}, reason {}'.format(self.logical_route, ','.join(e.args)))
            return self.to_string() + "... Failed"

    def _refresh_route(self):
        self.logical_route.source = self._updated_connections.get(self.logical_route.source, self.logical_route.source)
        self.logical_route.target = self._updated_connections.get(self.logical_route.target, self.logical_route.target)
        for port in self.logical_route.associated_ports:
            port.name = self._updated_connections.get(port.name, port.name)

    def to_string(self):
        return 'Create Route: {}'.format(self.logical_route)


class UpdateL1RouteAction(RemoveRouteAction, CreateRouteAction):
    def __init__(self, logical_route, logical_route_operations, updated_connections, logger):
        CreateRouteAction.__init__(self, logical_route, logical_route_operations, updated_connections, logger)

    def execute(self):
        # RemoveRouteAction.execute(self)
        # out = CreateRouteAction.execute(self)
        self._refresh_route()
        self.logger.debug("Update L1 route")
        try:
            for port in self.logical_route.associated_ports:
                self.logical_route_operations.add_resource(self.logical_route.reservation_id, port.name)
            return self.to_string() + "Done"
        except Exception as e:
            self.logger.error("Failed to update route for L1 resource, {}".format(e.args))
            return self.to_string() + "Failed"

    def to_string(self):
        return 'Update L1 Route: {}'.format(self.logical_route)


class UpdateRouteAction(RemoveRouteAction, CreateRouteAction):
    def __init__(self, logical_route, logical_route_operations, updated_connections, logger):
        CreateRouteAction.__init__(self, logical_route, logical_route_operations, updated_connections, logger)

    def execute(self):
        # RemoveRouteAction.execute(self)
        out = CreateRouteAction.execute(self)
        self._refresh_route()
        # for port in self.logical_route.associated_ports:
        # self.logical_route_operations.add_resource(self.logical_route.reservation_id, self.logical_route.so)
        # self.logical_route_operations.add_resource(self.logical_route.reservation_id, port.name)
        # return out

    def to_string(self):
        return 'Update Route: {}'.format(self.logical_route)
