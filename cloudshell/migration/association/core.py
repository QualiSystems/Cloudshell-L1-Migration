from abc import abstractmethod, ABCMeta


class Associator(object):
    __metaclass__ = ABCMeta

    def __init__(self):
        self.updated_connections = {}
        self.associations_table = {}

    def get_association(self, resource_pair):
        association = self._associate(resource_pair)
        self.associations_table.update(association.get_table())
        return association

    @abstractmethod
    def _associate(self, resource_pair):
        """
        :param cloudshell.migration.core.entities.ResourcesPair resource_pair:
        :rtype: Association
        :raises cloudshell.migration.exceptions.AssociationException: If cannot associate resources
        """
        pass


class Association(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def iter_pairs(self):
        """
        :rtype: collection.Iterable
        """
        pass

    @abstractmethod
    def get_associated(self, item):
        """
        :param cloudshell.migration.core.model.entities.AssociativeItem item:
        :rtype: cloudshell.migration.core.model.entities.AssociativeItem
        """
        pass

    @abstractmethod
    def get_table(self):
        """
        Associations table
        :rtype: dict[cloudshell.migration.core.model.entities.AssociativeItem, cloudshell.migration.core.model.entities.AssociativeItem]
        """
        pass

    @abstractmethod
    def valid(self):
        """
        :rtype: bool
        """
        pass
