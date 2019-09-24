import re

from backports.functools_lru_cache import lru_cache

from cloudshell.migration.association.helpers.association_helper import AssociationConfigHelper
from cloudshell.migration.exceptions import AssociationException


class StemBuilder(object):
    def __init__(self, logger):
        self._logger = logger

    def _build_address_stem(self, address, pattern):
        self._compile_pattern(pattern)
        match = re.search(pattern, address)
        if match:
            result = tuple(map(lambda x: x.zfill(2), match.groups() or [match.group(0)]))
            return result
        # self._logger.debug('Cannot match address {} for pattern {}'.format(address, pattern))

    def _build_name_stem(self, name, pattern):
        self._compile_pattern(pattern)
        match = re.search(pattern, name)
        if match:
            result = tuple(match.groups() or [match.group(0)])
            return result
        # self._logger.debug('Cannot match name {} for pattern {}'.format(name, pattern))

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
            address_stem = self._build_address_stem(ass_item.address,
                                                    ass_conf.address_pattern) if ass_conf.address_pattern else None
            name_stem = self._build_name_stem(ass_item.name, ass_conf.name_pattern) if ass_conf.name_pattern else None
            return address_stem, name_stem

    def build_table_for_item(self, configurations, item):
        """
        :param list[cloudshell.migration.association.model.AssociationConfig] configurations:
        :param cloudshell.migration.core.model.entities.AssociateItem item:
        :return:
        """

        self._logger.debug("Build stems for {}".format(item))
        address_stems = []
        name_stems = []
        for ass_conf in configurations:
            addr_stem, name_stem = self.build_stem(ass_conf, item)
            if addr_stem:
                address_stems.append(addr_stem)
            if name_stem:
                name_stems.append(name_stem)
        if not address_stems and not name_stems:
            raise AssociationException("No stems built for {}, {}".format(item, configurations))
        self._logger.debug("Address stems: {}, Name stems: {}".format(address_stems, name_stems))
        return address_stems, name_stems
