import collections
import os
from abc import ABCMeta, abstractmethod


class ActionsContainer(collections.Iterable):
    def __init__(self, actions=None):
        """
        :param collections.Iterable actions:
        """
        self.__actions_container = {}
        if actions:
            self._append_actions(actions)

    @property
    def sorted_actions(self):
        return sorted(self.actions, key=lambda a: a.priority)

    @property
    def actions(self):
        return self.__actions_container.values()

    def execute_actions(self):
        return map(lambda a: a.execute(), self.sorted_actions)

    # def update(self, container):
    #     """
    #     :type container: ActionsContainer
    #     """
    #     self._append_actions(container.actions)

    def append(self, actions):
        """
        :param collections.Iterable actions:
        :return:
        """
        self._append_actions(actions)

    def add(self, action):
        """
        :param Action action:
        """
        self._append_actions([action])

    def _append_actions(self, actions):
        """
        :param collections.Iterable[Action] actions:
        :rtype: dict[Actions,Actions]
        """
        for action in actions:
            handled_action = self.__actions_container.get(action)
            if handled_action and action is not handled_action:
                handled_action.merge(action)
            else:
                self.__actions_container[action] = action

    def to_string(self):
        out = ''
        for action in self.sorted_actions:
            out += action.to_string() + os.linesep
        return out

    # def is_empty(self):
    #     return len(self._actions_container) == 0

    def __str__(self):
        return self.to_string()

    def __iter__(self):
        return self.actions


class Action(object):
    __metaclass__ = ABCMeta

    class EXECUTION_PRIORITY:
        LOW = 1
        MIDDLE = 2
        HIGH = 3

    priority = EXECUTION_PRIORITY.LOW

    def __init__(self, logger):
        """
        :param logging.Logger logger:
        """
        self.logger = logger

    @abstractmethod
    def execute(self):
        """
        Execute action
        :return:
        """
        pass

    def merge(self, other):
        """
        Merge action
        :param Action other:
        """
        pass

    @abstractmethod
    def to_string(self):
        pass

    def __str__(self):
        return self.to_string()

    @abstractmethod
    def __eq__(self, other):
        pass

    @abstractmethod
    def __hash__(self):
        pass


class Initializer(object):
    __metaclass__ = ABCMeta

    def __init__(self, associator, operations_factory, configuration, logger):
        """
        :param cloudshell.migration.association.core.Associator associator:
        :param cloudshell.migration.core.operations.factory.OperationsFactory operations_factory:
        :param cloudshell.migration.configuration.config.Configuration configuration:
        :param logging.Logger logger:
        """
        self._associator = associator
        self._operations_factory = operations_factory
        self._configuration = configuration
        self._logger = logger

    @abstractmethod
    def initialize(self, resource_pair, override):
        """
        :param cloudshell.migration.core.model.entities.ResourcesPair resource_pair:
        :param bool override:
        :rtype: ActionsContainer
        """
        pass
