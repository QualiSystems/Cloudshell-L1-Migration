from abc import abstractmethod, ABCMeta


class Associator(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def associate(self):
        pass

    @abstractmethod
    def is_valid(self):
        pass
