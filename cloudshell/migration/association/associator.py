from collections import Counter

from backports.functools_lru_cache import lru_cache

from cloudshell.migration.association.model.abstract_associator import AbstractAssociator
from cloudshell.migration.association.services.config_parser import AssociationConfigTableParser
from cloudshell.migration.association.services.stem_builder import StemBuilder


class Associator(AbstractAssociator):

    def __init__(self, resource_pair, configuration, logger):
        """
        :param cloudshell.migration.core.model.entities.ResourcesPair resource_pair:
        :param cloudshell.migration.configuration.config.Configuration configuration:
        :param logging.Logger logger:
        """

        self.resource_pair = resource_pair
        self._configuration = configuration
        self._logger = logger
        self._stem_builder = StemBuilder(self._logger)

    @property
    @lru_cache()
    def _src_association_configuration(self):
        conf = self._configuration.get_association_configuration(
            self.resource_pair.src_resource.family, self.resource_pair.src_resource.model)
        return AssociationConfigTableParser.convert_to_resource_config_model(conf)

    @property
    @lru_cache()
    def _dst_association_configuration(self):
        conf = self._configuration.get_association_configuration(
            self.resource_pair.dst_resource.family, self.resource_pair.dst_resource.model)
        return AssociationConfigTableParser.convert_to_resource_config_model(conf)

    @property
    @lru_cache()
    def _dst_stem_table(self):
        return self._build_stem_table(self._dst_association_configuration, self.resource_pair.dst_resource.ports)

    def _build_stem_table(self, configuration, items):
        address_table = {}
        name_table = {}
        for conf in configuration:
            addr_stems, name_stems = self._stem_builder.build_table(conf, items)
            address_table.update(addr_stems)
            name_table.update(name_stems)
        return address_table, name_table

    def iter_pairs(self):
        for src_port in self.resource_pair.src_resource.ports:
            if src_port.connected_to:
                associated_dst_port = self.get_association(src_port)
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
            associated_dst_port = self.get_association(src_port)
            if associated_dst_port:
                association_table[src_port.name] = associated_dst_port.name
            else:
                self._logger.warning('Cannot find associated port for {}'.format(src_port))
        return association_table

    @lru_cache()
    def get_association(self, src_item):
        """
        :type src_item: cloudshell.migration.core.model.entities.AssociateItem
        :rtype: cloudshell.migration.core.model.entities.entities.AssociateItem
        """

        src_stems = []
        match_stems = []

        addr_stems, name_stems = self._build_stem_table(self._src_association_configuration, [src_item])

        match_addr_items = []
        match_name_items = []

        for stem in addr_stems:
            match_item = self._dst_stem_table[0].get(stem)
            if match_item:
                match_addr_items.append(match_item)

        for stem in name_stems:
            match_item = self._dst_stem_table[1].get(stem)
            if match_item:
                match_name_items.append(match_item)

        # match_addr_items = set(match_addr_items)
        # match_name_items = set(match_name_items)

        addr_cc = Counter(match_addr_items)

        name_cc = Counter(match_name_items)

        addr_rep = []
        max_num = 0
        for item, num_rep in addr_cc.items():
            if num_rep >= max_num:
                max_num = num_rep
                addr_rep.append(item)

        name_rep = []
        max_num = 0
        for item, num_rep in name_cc.items():
            if num_rep >= max_num:
                max_num = num_rep
                addr_rep.append(item)

        if addr_rep and name_rep:
            if addr_rep[-1] != name_rep[-1]:
                self._logger.warning('Address association not match name association')
            return addr_rep[-1]
        elif addr_rep:
            return addr_rep[-1]
        elif name_rep:
            return name_rep[-1]

        else:
            self._logger.warning('Association for {} not found'.format(str(src_item)))

    def valid(self):
        association_table = self.get_table()
        if len(association_table) == 0:
            return False
        if None in association_table.values():
            return False
        return True
