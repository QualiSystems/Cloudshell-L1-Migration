from collections import Counter

from backports.functools_lru_cache import lru_cache

from cloudshell.migration.association.model.abstract_associator import AbstractAssociator
from cloudshell.migration.association.services.config_parser import AssociationConfigTableParser
from cloudshell.migration.association.services.stem_builder import StemBuilder
from cloudshell.migration.exceptions import AssociationException


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
        conf = self._configuration.get_association_configuration(self.resource_pair.src_resource)
        return AssociationConfigTableParser.convert_to_resource_config_model(conf)

    @property
    @lru_cache()
    def _dst_association_configuration(self):
        conf = self._configuration.get_association_configuration(self.resource_pair.dst_resource)
        return AssociationConfigTableParser.convert_to_resource_config_model(conf)

    @property
    @lru_cache()
    def _dst_stem_table(self):
        self._logger.debug("Build stem table for Resource({})".format(self.resource_pair.dst_resource))
        return self._build_stem_table(self._dst_association_configuration, self.resource_pair.dst_resource.ports)

    def _update_stem_table(self, item, stems, table):
        for stem in stems:
            if stem in table:
                raise AssociationException(
                    "Stem {} related to {} already exist for {}".format(stem, item, table.get(stem)))
            table[stem] = item
        return table

    def _build_stem_table(self, configuration, items):
        address_table = {}
        name_table = {}
        for item in items:
            addr_stems, name_stems = self._stem_builder.build_table_for_item(configuration, item)
            self._update_stem_table(item, addr_stems, address_table)
            self._update_stem_table(item, name_stems, name_table)
        return address_table, name_table

    def iter_pairs(self):
        """
        :rtype: collections.Iterable[(cloudshell.migration.core.model.entities.AssociateItem,cloudshell.migration.core.model.entities.AssociateItem)]
        """
        for src_port in self.resource_pair.src_resource.ports:
            # if src_port.connected_to:
            associated_dst_port = self.get_associated(src_port)
            if associated_dst_port:
                yield src_port, associated_dst_port
            else:
                self._logger.warning('Cannot find associated port for {}'.format(src_port))

    @lru_cache()
    def get_associated(self, src_item):
        """
        :type src_item: cloudshell.migration.core.model.entities.AssociateItem
        :rtype: cloudshell.migration.core.model.entities.AssociateItem
        """

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

        dst_item = None
        if addr_rep and name_rep:
            self._logger.debug('Association found by address and name pattern.')
            if addr_rep[-1] != name_rep[-1]:
                self._logger.warning('Address association do not match name association.')
            dst_item = addr_rep[-1]
        elif addr_rep:
            self._logger.debug('Association found by address pattern.')
            dst_item = addr_rep[-1]
        elif name_rep:
            self._logger.debug('Association found by name pattern.')
            dst_item = name_rep[-1]
        else:
            self._logger.warning('Association not found for {}'.format(str(src_item)))

        if dst_item:
            self.global_association_table[src_item.name] = dst_item.name
        return dst_item

    @property
    @lru_cache()
    def association_table(self):
        """
        Associations table
        :rtype: dict[cloudshell.migration.core.model.entities.AssociateItem, cloudshell.migration.core.model.entities.AssociateItem]
        """
        return dict(self.iter_pairs())

    def valid(self):
        if len(self.association_table) == 0:
            return False
        if None in self.association_table.values():
            return False
        return True
