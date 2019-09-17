from functools import total_ordering

from cloudshell.migration.core.model.entities import AssociateItem


class AssociationConfig(object):
    def __init__(self, name, family, model, address_pattern, name_pattern):
        """
        :param str name:
        :param list[str] family:
        :param list[str] model:
        :param str address_pattern:
        :param str name_pattern:
        """
        self.name = name
        self.family = family
        self.model = model
        self.address_pattern = address_pattern
        self.name_pattern = name_pattern


# @total_ordering
# class AssociationStem(object):
#     def __init__(self, conf, address_stem, name_stem, item):
#         """
#         :param AssociationConfig conf:
#         :param tuple address_stem:
#         :param tuple name_stem:
#         :param cloudshell.migration.core.model.entities.AssociateItem item:
#         """
#         self.conf_name = conf
#         self.address_stem = address_stem
#         self.name_stem = name_stem
#         self.item = item
#
#     def __hash__(self):
#         return hash(self.address_stem) | hash(self.name_stem)
#
#     def __eq__(self, other):
#         """
#         :param AssociationStem other:
#         """
#         return self.equals_by_address_stem(other) and self.equals_by_name_stem(other)
#
#     def __gt__(self, other):
#         """
#         :param AssociationStem other:
#         """
#         return self.equals_by_address_stem(other) and not self.equals_by_name_stem(other)
#
#     def equals_by_address_stem(self, other):
#         """
#         :param AssociationStem other:
#         """
#         return self.address_stem == other.address_stem
#
#     def equals_by_name_stem(self, other):
#         """
#         :param AssociationStem other:
#         """
#         return self.name_stem == other.name_stem


# @total_ordering
class AssociationStem(object):
    def __init__(self, conf, stem, item):
        """
        :param AssociationConfig conf:
        :param tuple stem:
        :param cloudshell.migration.core.model.entities.AssociateItem item:
        """
        self.conf_name = conf
        self.stem = stem
        self.item = item

    def __hash__(self):
        return hash(self.stem)

    def __eq__(self, other):
        """
        :param AssociationStem other:
        """
        return self.stem == other.stem


class ItemMatch(object):
    def __init__(self, stem, src_item, target_item):
        """
        :param stem:
        :param src_item:
        :param target_item:
        """
        self.stem = stem
        self.src_item = src_item
        self.target_item = target_item
