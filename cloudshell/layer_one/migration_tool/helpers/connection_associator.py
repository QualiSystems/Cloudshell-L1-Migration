from cloudshell.layer_one.migration_tool.entities.connection import Connection


class ConnectionAssociator(object):
    def __init__(self, ports, logger):
        """
        :type logger: cloudshell.layer_one.migration_tool.helpers.logger.Logger
        """
        self._ports = ports
        self._logger = logger
        self._ports_sorted_by_associated_address = None

    @property
    def port_sorted_by_associated_address(self):
        if not self._ports_sorted_by_associated_address:
            self._ports_sorted_by_associated_address = {self._associated_address(port.address): port for port in
                                                        self._ports}
        return self._ports_sorted_by_associated_address

    def associated_connection(self, connection):
        """
        :type connection: cloudshell.layer_one.migration_tool.entities.connection.Connection
        """
        associated_port = self.port_sorted_by_associated_address.get(connection.port.address)
        if associated_port:
            return Connection(associated_port, connection.connected_to, connection.weight)
        else:
            self._logger.error('Cannot find associated port, for {}'.format(connection))

    def _associated_address(self, address):
        return address
