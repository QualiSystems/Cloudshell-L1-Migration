from abc import abstractmethod, ABCMeta


class AbstractAssociator(object):
    __metaclass__ = ABCMeta

    global_association_table = {}

    @abstractmethod
    def iter_pairs(self):
        """
        :rtype: collection.Iterable
        """
        pass

    @abstractmethod
    def get_associated(self, item):
        """
        :param cloudshell.migration.core.model.entities.AssociateItem item:
        :rtype: cloudshell.migration.core.model.entities.AssociateItem
        """
        pass

    @abstractmethod
    def valid(self):
        """
        :rtype: bool
        """
        pass
