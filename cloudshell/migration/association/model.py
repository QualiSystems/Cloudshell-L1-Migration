class AssociationItemConfig(object):
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


class AssociationItemStem(object):
    def __init__(self, address_stem, name_stem):
        self.address_stem = address_stem
        self.name_stem = name_stem
