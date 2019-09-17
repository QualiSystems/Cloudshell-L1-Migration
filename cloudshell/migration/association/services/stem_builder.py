import re

from backports.functools_lru_cache import lru_cache

from cloudshell.migration.association.helpers.association_helper import AssociationConfigHelper
from cloudshell.migration.association.model.entities import AssociationStem


class StemBuilder(object):
    def __init__(self, logger):
        self._logger = logger

    def _build_address_stem(self, address, pattern):
        match = re.search(pattern, address)
        if match:
            result = tuple(map(lambda x: x.zfill(2), match.groups() or [match.group(0)]))
            return result
        self._logger.error('Cannot match address {} for pattern {}'.format(address, pattern.pattern))

    def _build_name_stem(self, address, pattern):
        match = re.search(pattern, address)
        if match:
            result = tuple(match.groups() or [match.group(0)])
            return result
        self._logger.error('Cannot match address {} for pattern {}'.format(address, pattern.pattern))

    @staticmethod
    @lru_cache()
    def _compile_pattern(pattern):
        if pattern:
            return re.compile(pattern, re.IGNORECASE)

    def build_stem(self, ass_conf, ass_item):
        """
        :param cloudshell.migration.association.model.entities.AssociationConfig ass_conf:
        :param cloudshell.migration.core.model.entities.AssociateItem ass_item:
        :return:
        """

        if AssociationConfigHelper.match_to_item_config(ass_item, ass_conf):
            address_pattern = self._compile_pattern(ass_conf.address_pattern)
            name_pattern = self._compile_pattern(ass_conf.name_pattern)
            address_stem = self._build_address_stem(ass_item.address, address_pattern)
            name_stem = self._build_name_stem(ass_item.name, name_pattern)
            # if address_stem or name_stem:
            #     stem = AssociationStem(ass_conf, address_stem, name_stem, ass_item)
            #     return stem
            # if address_stem:
            #     address_stem = AssociationStem(ass_conf, a)
            return address_stem, name_stem

    def build_table(self, ass_conf, item_list):
        """
        :param cloudshell.migration.association.model.AssociationConfig ass_conf:
        :param list[cloudshell.migration.core.model.entities.AssociateItem] item_list:
        :return:
        """

        address_table = {}
        name_table = {}
        for item in item_list:
            addr_stem, name_stem = self.build_stem(ass_conf, item)
            if addr_stem:
                address_table[addr_stem] = item
            if name_stem:
                name_table[name_stem] = item
        return address_table, name_table
