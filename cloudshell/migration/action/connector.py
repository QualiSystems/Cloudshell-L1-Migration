from abc import ABCMeta

from cloudshell.migration.action.core import Action


class UpdateConnectorAction(Action):
    ACTION_DESCR = "Update Connector"

    priority = Action._EXECUTION_STAGE.THREE

    def __init__(self, connector, connector_operations, associations_table, logger):
        """
        :param loudshell.migration.core.model.entities import Connector connector:
        :param cloudshell.migration.core.operations.connector.ConnectorOperations connector_operations:
        :param dict associations_table:
        :param logging.Logger logger
        """
        super(UpdateConnectorAction, self).__init__(logger)
        self.connector = connector
        self.connector_operations = connector_operations
        self._associations_table = associations_table

    def __hash__(self):
        return hash(self.connector)

    def __eq__(self, other):
        return Action.__eq__(self, other) and self.connector == other.connector

    def description(self):
        return '{} {}'.format(self.ACTION_DESCR, self.connector)

    def execute(self):
        self._logger.debug("Removing connector {}".format(self.connector))
        try:
            self.connector_operations.remove_connector(self.connector)
        except:
            self._logger.exception("Cannot remove connector:")
        self.connector.source = self._associations_table.get(self.connector.source, self.connector.source)
        self.connector.target = self._associations_table.get(self.connector.target, self.connector.target)
        self._logger.debug("Creating connector {}".format(self.connector))
        self.connector_operations.update_connector(self.connector)
