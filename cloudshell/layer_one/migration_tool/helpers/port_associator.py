import re

from backports.functools_lru_cache import lru_cache


class PortAssociator(object):
    def __init__(self, dst_ports, src_port_pattern, dst_port_pattern, logger):
        """
        :type logger: cloudshell.layer_one.migration_tool.helpers.logger.Logger
        """
        self._dst_ports = dst_ports
        self._logger = logger
        self._src_port_pattern = src_port_pattern
        self._dst_port_pattern = dst_port_pattern

    @property
    @lru_cache()
    def dst_port_sorted_by_associated_address(self):
        return {self._format_dst_address(port.address): port for port in self._dst_ports}

    @property
    @lru_cache()
    def dst_port_sorted_by_name(self):
        return {self._format_name(port.name): port for port in self._dst_ports}

    def associated_port(self, src_port):
        """
        :type src_port: cloudshell.layer_one.migration_tool.entities.Port
        """
        dst_port = self.dst_port_sorted_by_associated_address.get(
            self._format_src_address(src_port.address)) or self.dst_port_sorted_by_name.get(
            self._format_name(src_port.name))

        if dst_port:
            return dst_port
        else:
            self._logger.error('Cannot find associated DST port, for {}'.format(src_port))

    def _format_dst_address(self, address):
        # self._logger.debug('Matching new address {} for pattern {}'.format(address, self._dst_port_pattern))
        return self._format_address(address, self._dst_port_pattern)

    def _format_src_address(self, address):
        # self._logger.debug('Matching old address {} for pattern {}'.format(address, self._src_port_pattern))
        return self._format_address(address, self._src_port_pattern)

    def _format_address(self, address, pattern):
        match = re.search(pattern, address, flags=re.IGNORECASE)
        if match:
            x = tuple(map(lambda x: x.zfill(2), match.groups()))
            return x
        self._logger.error('Cannot match address {} for pattern {}'.format(address, pattern))

    def _format_name(self, name):
        """
        :param str name:
        :rtype: str
        """
        return "/".join(name.split("/")[1:])
