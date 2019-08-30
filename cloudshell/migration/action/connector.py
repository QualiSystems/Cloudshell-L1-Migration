from abc import ABCMeta

from cloudshell.migration.action.core import Action


class ConnectorAction(Action):
    __metaclass__ = ABCMeta

    priority = Action.EXECUTION_PRIORITY.LOW

    def __init__(self, connector, route_connector_operations, logger):
        """
        :type connector:
        :type route_connector_operations: cloudshell.migration.operations.route_operations.RouteConnectorOperations
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
            self.logger.error('Cannot remove connector {}, reason {}'.format(self.connector, str(e)))
            return self.to_string() + "... Failed"

    def to_string(self):
        return "Remove Connector: {}".format(self.connector)


class CreateConnectorAction(ConnectorAction):
    def __init__(self, connector, route_connector_operations, associations_table, logger):
        """
        :type connector:
        :type route_connector_operations: cloudshell.migration.operations.route_operations.RouteConnectorOperations
        :type associations_table: dict
        :type logger: cloudshell.migration.helpers.log_helper.Logger
        """
        super(CreateConnectorAction, self).__init__(connector, route_connector_operations, logger)
        self._associations_table = associations_table

    def execute(self):
        self.connector.source = self._associations_table.get(self.connector.source, self.connector.source)
        self.connector.target = self._associations_table.get(self.connector.target, self.connector.target)
        self.logger.debug("Creating connector {}".format(self.connector))
        try:
            self.route_connector_operations.update_connector(self.connector)
            return self.to_string() + " ... Done"
        except Exception as e:
            self.logger.error('Cannot create connector {}, reason {}'.format(self.connector, str(e)))
            return self.to_string() + "... Failed"

    def to_string(self):
        return "Create Connector: {}".format(self.connector)


class UpdateConnectorAction(RemoveConnectorAction, CreateConnectorAction):
    def __init__(self, connector, route_connector_operations, associations_table, logger):
        """
        :type connector:
        :type route_connector_operations: cloudshell.migration.operations.route_operations.RouteConnectorOperations
        :type associations_table: dict
        :type logger: cloudshell.migration.helpers.log_helper.Logger
        """
        CreateConnectorAction.__init__(self, connector, route_connector_operations, associations_table, logger)

    def execute(self):
        RemoveConnectorAction.execute(self)
        out = CreateConnectorAction.execute(self)
        return out

    def to_string(self):
        return 'Update Connector: {}'.format(self.connector)

