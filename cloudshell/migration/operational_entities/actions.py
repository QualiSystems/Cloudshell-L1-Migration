import os
from abc import ABCMeta, abstractmethod

from cloudshell.migration.operations.blueprint_operations import PackageOperations


class ActionsContainer(object):
    def __init__(self, remove_routes=None, update_connections=None, create_routes=None, remove_connectors=None,
                 create_connectors=None, blueprint_actions=None):
        self.remove_routes = remove_routes or []
        self.update_connections = update_connections or []
        self.create_routes = create_routes or []
        self.remove_connectors = remove_connectors or []
        self.create_connectors = create_connectors or []
        self.blueprint_actions = blueprint_actions or []

    def sequence(self):
        sequence = []
        sequence.extend(set(self.remove_routes))
        sequence.extend(set(self.remove_connectors))
        sequence.extend(set(self.update_connections))
        sequence.extend(set(self.create_routes))
        sequence.extend(set(self.create_connectors))
        sequence.extend(set(self.blueprint_actions))
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
        self.remove_connectors = set(self.remove_connectors) | set(container.remove_connectors)
        self.create_connectors = set(self.create_connectors) | set(container.create_connectors)
        self._update_blieprint_actions(container.blueprint_actions)

    def _update_blieprint_actions(self, blueprint_actions):
        for action in blueprint_actions:
            if action in self.blueprint_actions:
                self.blueprint_actions[self.blueprint_actions.index(action)].merge(action)
            else:
                self.blueprint_actions.append(action)

    def to_string(self):
        out = ''
        for action in self.sequence():
            out += action.to_string() + os.linesep
        return out

    def is_empty(self):
        return False if self.remove_routes or self.update_connections or self.create_routes or self.create_connectors or self.remove_connectors or self.blueprint_actions else True

    def __str__(self):
        return self.to_string()


class Action(object):
    __metaclass__ = ABCMeta

    def __init__(self, logger):
        """
        :type logger: cloudshell.migration.helpers.log_helper.Logger
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
        :type logical_route:  cloudshell.migration.entities.LogicalRoute
        :type logical_route_operations: cloudshell.migration.operations.route_connector_operations.RouteConnectorOperations
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

    def to_string(self):
        return 'Create Route: {}'.format(self.logical_route)


class UpdateConnectionAction(Action):
    def __init__(self, src_port, dst_port, resource_operations, updated_connections, logger):
        """
        :type src_port: cloudshell.migration.entities.Port
        :type dst_port: cloudshell.migration.entities.Port
        :type resource_operations: cloudshell.migration.operations.resource_operations.ResourceOperations
        :type updated_connections: dict
        :type logger: cloudshell.migration.helpers.log_helper.Logger
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
            return self.to_string() + " ... Done"
        except Exception as e:
            self.logger.error('Cannot update port {}, reason {}'.format(self.dst_port, str(e)))
            return self.to_string() + "... Failed"

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


class ConnectorAction(Action):
    def __init__(self, connector, route_connector_operations, logger):
        """
        :type connector:
        :type route_connector_operations: cloudshell.migration.operations.route_connector_operations.RouteConnectorOperations
        :type logger: cloudshell.migration.helpers.log_helper.Logger
        """
        super(ConnectorAction, self).__init__(logger)
        self.connector = connector
        self.route_connector_operations = route_connector_operations

    def __hash__(self):
        return hash(self.connector)

    def __eq__(self, other):
        return self.connector == other.connector


class RemoveConnectorAction(ConnectorAction):
    def execute(self):
        self.logger.debug("Removing connector {}".format(self.connector))
        try:
            self.route_connector_operations.remove_connector(self.connector)
            return self.to_string() + " ... Done"
        except Exception as e:
            pass

    def to_string(self):
        return "Remove Connector: {}".format(self.connector)


class CreateConnectorAction(ConnectorAction):
    def __init__(self, connector, route_connector_operations, updated_connections, logger):
        """
        :type connector:
        :type route_connector_operations: cloudshell.migration.operations.route_connector_operations.RouteConnectorOperations
        :type updated_connections: dict
        :type logger: cloudshell.migration.helpers.log_helper.Logger
        """
        super(CreateConnectorAction, self).__init__(connector, route_connector_operations, logger)
        self._updated_connections = updated_connections

    def execute(self):
        self.connector.source = self._updated_connections.get(self.connector.source, self.connector.source)
        self.connector.target = self._updated_connections.get(self.connector.target, self.connector.target)
        self.logger.debug("Creating connector {}".format(self.connector))
        try:
            self.route_connector_operations.update_connector(self.connector)
            return self.to_string() + " ... Done"
        except Exception as e:
            pass

    def to_string(self):
        return "Create Connector: {}".format(self.connector)


class BlueprintAction(Action):
    def __init__(self, blueprint_name, routes, connectors, quali_api, updated_connections, logger):
        super(BlueprintAction, self).__init__(logger)
        self.blueprint_name = blueprint_name
        self.routes = routes
        self.connectors = connectors
        self.quali_api = quali_api
        self._updated_connections = updated_connections

    def execute(self):
        package_operations = PackageOperations(self.quali_api, self.logger)
        package_operations.load_package(self.blueprint_name)
        for ent in list(self.routes) + list(self.connectors):
            self.logger.debug('Remove : {}'.format(ent))
            package_operations.remove_route_connector(ent.source, ent.target)
        self._update_endpoints(self.routes)
        self._update_endpoints(self.connectors)
        for route in self.routes:
            self.logger.debug('Add {}'.format(route))
            package_operations.add_route(route)

        for connector in self.connectors:
            self.logger.debug('Add {}'.format(connector))
            package_operations.add_connector(connector)

        package_operations.update_topology()
        return self.to_string() + " ... Done"

    def _update_endpoints(self, ent_list):
        for ent in ent_list:
            ent.source = self._updated_connections.get(ent.source, ent.source)
            ent.target = self._updated_connections.get(ent.target, ent.target)

    def to_string(self):
        return "Update Blueprint: {}".format(self.blueprint_name)

    def __hash__(self):
        return hash(self.blueprint_name)

    def __eq__(self, other):
        return self.blueprint_name == other.blueprint_name

    def merge(self, action):
        """
        :param BlueprintAction action:
        """
        self.routes = set(self.routes) | set(action.routes)
        self.connectors = set(self.connectors) | set(action.connectors)
