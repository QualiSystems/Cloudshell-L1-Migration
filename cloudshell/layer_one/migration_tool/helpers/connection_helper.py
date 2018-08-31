class ConnectionHelper(object):
    def __init__(self, api, logger, dry_run):
        """
        :type api: cloudshell.api.cloudshell_api.CloudShellAPISession
        :type logger: cloudshell.layer_one.migration_tool.helpers.logger.Logger
        """
        self._api = api
        self._logger = logger
        self._dry_run = dry_run

    def update_connection(self, connection):
        """
        :type connection: cloudshell.layer_one.migration_tool.entities.connection.Connection
        """
        self._logger.debug('Updating Connection {}=>{}'.format(connection.port.name, connection.connected_to))
        if not self._dry_run:
            self._api.UpdatePhysicalConnection(connection.port.name, connection.connected_to)
            self._api.UpdateConnectionWeight(connection.port.name, connection.connected_to, connection.weight)
