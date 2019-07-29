from cloudshell.migration.operations.operations import Operations


class ConnectionOperations(Operations):
    def update_connection(self, port):
        """
        :type port: cloudshell.migration.entities.Port
        """
        self._logger.info('---- Updating Connection {}=>{}'.format(port.name, port.connected_to))
        if not self._dry_run:
            self._api.UpdatePhysicalConnection(port.name, port.connected_to or '')
            if port.connected_to and port.connection_weight:
                self._api.UpdateConnectionWeight(port.name, port.connected_to, port.connection_weight)
