import re

from backports.functools_lru_cache import lru_cache


class PortAssociator(object):
    def __init__(self, src_resource, dst_resource, config_operations, logger):
        """
        :type src_resource: cloudshell.migration.entities.Resource
        :type dst_resource: cloudshell.migration.entities.Resource
        :type config_operations: cloudshell.migration.operations.config_operations.ConfigOperations
        :type logger: cloudshell.migration.helpers.log_helper.Logger
        """

        self._src_resource = src_resource
        self._dst_resource = dst_resource
        self._config_operations = config_operations
        self._logger = logger

        self._src_association_configuration = self._config_operations.get_association_configuration(
            self._src_resource.family, self._src_resource.model)
        self._dst_association_configuration = self._config_operations.get_association_configuration(
            self._dst_resource.family, self._dst_resource.model)

        self._src_port_pattern = re.compile(
            self._src_association_configuration.get(self._config_operations.KEY.PATTERN),
            re.IGNORECASE)
        self._dst_port_pattern = re.compile(
            self._dst_association_configuration.get(self._config_operations.KEY.PATTERN),
            re.IGNORECASE)

    @property
    @lru_cache()
    def _dst_port_sorted_by_associated_address(self):
        address_dict = {}
        for port in self._dst_resource.ports:
            f_addr = self._format_dst_address(port.address)
            if f_addr:
                address_dict[f_addr] = port
        return address_dict

    @property
    @lru_cache()
    def _dst_port_sorted_by_name(self):
        return {self._format_name(port.name): port for port in self._dst_resource.ports}

    @property
    @lru_cache()
    def _dst_port_sorted_by_port_name(self):
        return {self._format_port_name(port.name): port for port in self._dst_resource.ports}

    def associated_pairs(self):
        for src_port in self._src_resource.ports:
            if src_port.connected_to:
                associated_dst_port = self.associate_dst_port(src_port)
                if associated_dst_port:
                    yield src_port, associated_dst_port

    def associate_dst_port(self, src_port):
        """
        :type src_port: cloudshell.migration.entities.Port
        """
        result_list = []
        if self._dst_association_configuration.get(self._config_operations.KEY.ASSOCIATE_BY_ADDRESS, True):
            dst_port_by_address = self._dst_port_sorted_by_associated_address.get(
                self._format_src_address(src_port.address))
            if dst_port_by_address:
                result_list.append(dst_port_by_address)

        if self._dst_association_configuration.get(self._config_operations.KEY.ASSOCIATE_BY_NAME, False):
            dst_port_by_name = self._dst_port_sorted_by_name.get(self._format_name(src_port.name))
            if dst_port_by_name:
                result_list.append(dst_port_by_name)

        if self._dst_association_configuration.get(self._config_operations.KEY.ASSOCIATE_BY_PORT_NAME, False):
            dst_port_by_port_name = self._dst_port_sorted_by_port_name.get(self._format_port_name(src_port.name))
            if dst_port_by_port_name:
                result_list.append(dst_port_by_port_name)

        if not result_list:
            self._logger.error('Cannot find associated DST port, for {}'.format(src_port))
        elif len(set(result_list)) > 1:
            self._logger.warning('Multiple associations {} for {}'.format(result_list, src_port))
            return result_list[0]
        else:
            self._logger.debug('Association found {} -> {}'.format(src_port, result_list[0]))
            return result_list[0]

    def _format_dst_address(self, address):
        self._logger.debug('Matching dst address {} for pattern {}'.format(address, self._dst_port_pattern.pattern))
        return self._format_address(address, self._dst_port_pattern)

    def _format_src_address(self, address):
        self._logger.debug('Matching src address {} for pattern {}'.format(address, self._src_port_pattern.pattern))
        return self._format_address(address, self._src_port_pattern)

    def _format_address(self, address, pattern):
        match = re.search(pattern, address)
        if match:
            x = tuple(map(lambda x: x.zfill(2), match.groups()))
            return x
        self._logger.error('Cannot match address {} for pattern {}'.format(address, pattern.pattern))

    def _format_name(self, name):
        """
        :param str name:
        :rtype: str
        """
        return "/".join(name.split("/")[1:])

    def _format_port_name(self, port_name):
        """
        :param str port_name:
        :rtype: str
        """
        return port_name.split("/")[-1]
