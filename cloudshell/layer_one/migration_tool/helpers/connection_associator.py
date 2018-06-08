import re

from cloudshell.layer_one.migration_tool.entities.connection import Connection


class ConnectionAssociator(object):
    def __init__(self, ports, logger, old_port_pattern, new_port_pattern):
        """
        :type logger: cloudshell.layer_one.migration_tool.helpers.logger.Logger
        """
        self._ports = ports
        self._logger = logger
        self._old_port_pattern = old_port_pattern
        self._new_port_pattern = new_port_pattern
        self._ports_sorted_by_associated_address = None

    @property
    def port_sorted_by_associated_address(self):
        if not self._ports_sorted_by_associated_address:
            self._ports_sorted_by_associated_address = {self._associate_new_address(port.address): port for port in
                                                        self._ports}
        return self._ports_sorted_by_associated_address

    def associated_connection(self, connection):
        """
        :type connection: cloudshell.layer_one.migration_tool.entities.connection.Connection
        """
        associated_port = self.port_sorted_by_associated_address.get(
            self._associate_old_address(connection.port.address))
        if associated_port:
            return Connection(associated_port, connection.connected_to, connection.weight)
        else:
            self._logger.error('Cannot find associated port, for {}'.format(connection))

    def _associate_new_address(self, address):
        match = re.search(self._new_port_pattern, address, flags=re.IGNORECASE)
        return match.groups()

    def _associate_old_address(self, address):
        match = re.search(self._old_port_pattern, address, flags=re.IGNORECASE)
        return match.groups()
