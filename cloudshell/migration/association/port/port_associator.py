import re
from backports.functools_lru_cache import lru_cache

from cloudshell.migration.association.core import Associator, Association
from cloudshell.migration.exceptions import AssociationException


class PortAssociator(Associator):
    def __init__(self, configuration, logger):
        """
        :param cloudshell.migration.configuration.config.Configuration configuration:
        :param cloudshell.migration.helpers.log_helper.Logger logger:
        """

        super(PortAssociator, self).__init__()
        self._configuration = configuration
        self._logger = logger

    @lru_cache()
    def _associate(self, resource_pair):
        association = PortAssociation(resource_pair, self._configuration, self._logger)
        if not association.valid():
            raise AssociationException("Cannot associate pair {}".format(resource_pair))
        return association


class PortAssociation(Association):

    def __init__(self, resource_pair, configuration, logger):
        """
        :param cloudshell.migration.core.model.entities.ResourcesPair resource_pair:
        :param cloudshell.migration.configuration.config.Configuration configuration:
        :param logging.Logger logger:
        """

        self.resource_pair = resource_pair
        self._configuration = configuration
        self._logger = logger

    @property
    @lru_cache()
    def _src_association_configuration(self):
        return self._configuration.get_association_configuration(
            self.resource_pair.src_resource.family, self.resource_pair.src_resource.model)

    @property
    @lru_cache()
    def _dst_association_configuration(self):
        return self._configuration.get_association_configuration(
            self.resource_pair.dst_resource.family, self.resource_pair.dst_resource.model)

    @property
    @lru_cache()
    def _src_port_pattern(self):
        return re.compile(
            self._src_association_configuration.get(self._configuration.KEY.PATTERN),
            re.IGNORECASE)

    @property
    @lru_cache()
    def _dst_port_pattern(self):
        return re.compile(
            self._dst_association_configuration.get(self._configuration.KEY.PATTERN),
            re.IGNORECASE)

    @property
    @lru_cache()
    def _dst_port_sorted_by_associated_address(self):
        address_dict = {}
        for port in self.resource_pair.dst_resource.ports:
            f_addr = self._format_dst_address(port.address)
            if f_addr:
                address_dict[f_addr] = port
        return address_dict

    @property
    @lru_cache()
    def _dst_port_sorted_by_name(self):
        return {self._format_name(port.name): port for port in self.resource_pair.dst_resource.ports}

    @property
    @lru_cache()
    def _dst_port_sorted_by_port_name(self):
        return {self._format_port_name(port.name): port for port in self.resource_pair.dst_resource.ports}

    def iter_pairs(self):
        for src_port in self.resource_pair.src_resource.ports:
            if src_port.connected_to:
                associated_dst_port = self.get_associated(src_port)
                if associated_dst_port:
                    yield src_port, associated_dst_port
                else:
                    self._logger.warning('Cannot find associated port for {}'.format(src_port))

    @lru_cache()
    def get_table(self):
        """
        :rtype: dict
        """
        association_table = {}
        for src_port in self.resource_pair.src_resource.ports:
            associated_dst_port = self.get_associated(src_port)
            if associated_dst_port:
                association_table[src_port.name] = associated_dst_port.name
            else:
                self._logger.warning('Cannot find associated port for {}'.format(src_port))
        return association_table

    @lru_cache()
    def get_associated(self, src_port):
        """
        :type src_port: cloudshell.migration.core.model.entities.Port
        :rtype: cloudshell.migration.core.model.entities.Port
        """
        result_list = []
        if self._dst_association_configuration.get(self._configuration.KEY.ASSOCIATE_BY_ADDRESS, True):
            dst_port_by_address = self._dst_port_sorted_by_associated_address.get(
                self._format_src_address(src_port.address))
            if dst_port_by_address:
                result_list.append(dst_port_by_address)

        if self._dst_association_configuration.get(self._configuration.KEY.ASSOCIATE_BY_NAME, False):
            dst_port_by_name = self._dst_port_sorted_by_name.get(self._format_name(src_port.name))
            if dst_port_by_name:
                result_list.append(dst_port_by_name)

        if self._dst_association_configuration.get(self._configuration.KEY.ASSOCIATE_BY_PORT_NAME, False):
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
            result = tuple(map(lambda x: x.zfill(2), match.groups()))
            return result
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

    def valid(self):
        association_table = self.get_table()
        if len(association_table) == 0:
            return False
        if None in association_table.values():
            return False
        return True
