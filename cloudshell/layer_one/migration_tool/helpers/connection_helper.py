class ConnectionHelper(object):
    def __init__(self, api, logger):
        """
        :type api: cloudshell.api.cloudshell_api.CloudShellAPISession
        :type logger: cloudshell.layer_one.migration_tool.helpers.logger.Logger
        """
        self._api = api
        self._logger = logger

    def update_connection(self, connection):
        """
        :type connection: cloudshell.layer_one.migration_tool.entities.connection.Connection
        """
        self._api.UpdatePhysicalConnection(connection.port.name, connection.connected_to)
