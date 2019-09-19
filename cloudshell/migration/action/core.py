import collections
import os
from abc import ABCMeta, abstractmethod


class ActionsContainer(collections.Iterable):
    def __init__(self, actions=None):
        """
        :param collections.Iterable actions:
        """
        self.__actions_container = {}
        """:type : dict"""
        if actions:
            self._append_actions(actions)
        self._results = {}

    @property
    def sorted_actions(self):
        """
        :rtype: list[cloudshell.migration.action.core.Action]
        """
        return sorted(self.actions, key=lambda a: a.priority)

    @property
    def actions(self):
        """
        :rtype: list[cloudshell.migration.action.core.Action]
        """
        return self.__actions_container.values()

    def extend(self, actions):
        """
        :param collections.Iterable actions:
        """
        self._append_actions(actions)

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
            out += str(action) + os.linesep
        return out

    # def is_empty(self):
    #     return len(self._actions_container) == 0

    def __str__(self):
        return self.to_string()

    def __iter__(self):
        return self.actions.__iter__()


class Action(object):
    __metaclass__ = ABCMeta
    ACTION_DESCR = "Action"

    class _EXECUTION_STAGE:
        FOUR = 4
        THREE = 3
        TWO = 2
        ONE = 1

    class EXECUTION_STATE:
        NOT_EXECUTED = "NOT EXECUTED"
        SUCCESS = "SUCCESSFUL"
        FAILED = "FAILED"

    priority = _EXECUTION_STAGE.FOUR
    rollback_on_failure = True
    rollback_exceptions = [Exception]

    def __init__(self, logger):
        """
        :param logging.Logger logger:
        """
        self._logger = logger
        self._execution_state = self.EXECUTION_STATE.NOT_EXECUTED

    @abstractmethod
    def execute(self):
        """
        Main action flow
        """
        pass

    def rollback(self):
        """
        Rollback flow, execute if main flow failed with exception defined in
        """
        pass

    def merge(self, other):
        """
        Merge action
        :param Action other:
        """
        pass

    @property
    def execution_state(self):
        """:rtype: cloudshell.migration.action.core.Action.EXECUTION_STATE"""
        return self._execution_state

    @execution_state.setter
    def execution_state(self, state):
        """
        :param cloudshell.migration.action.core.Action.EXECUTION_STATE state:
        """
        self._execution_state = state

    def description(self):
        return self.ACTION_DESCR

    @staticmethod
    def initialize_for_pair(resource_pair, override, associations_table, operations_factory, logger):
        """
        :param cloudshell.migration.core.model.entities.ResourcesPair resource_pair:
        :param bool override:
        :param dict associations_table:
        :param cloudshell.migration.core.operations.factory.OperationsFactory operations_factory:
        :param logging.Logger logger:
        :rtype: ActionsContainer
        """
        pass

    def __str__(self):
        return "{} - {}".format(self.description(), self.execution_state)

    def __eq__(self, other):
        return isinstance(other, self.__class__)

    @abstractmethod
    def __hash__(self):
        pass


class ActionExecutor(object):
    def __init__(self, logger):
        """
        :param logging.Logger logger:
        """
        self._logger = logger
        self.no_error = True

    def iter_execution(self, action_container):
        """
        :param cloudshell.migration.action.core.ActionsContainer action_container:
        :rtype: collections.Iterable[cloudshell.migration.action.core.Action]
        """
        for action in action_container.sorted_actions:
            self._logger.debug('Executing {}'.format(action))
            try:
                action.execute()
                action.execution_state = action.EXECUTION_STATE.SUCCESS
                self._logger.debug("Executed {}".format(action))
            except Exception as e:
                self._logger.exception("Action execution failed:")
                action.execution_state = action.EXECUTION_STATE.FAILED
                self.no_error = False

                if action.rollback_on_failure and isinstance(e, tuple(action.rollback_exceptions)):
                    self._logger.debug("Rollback")
                    try:
                        action.rollback()
                    except:
                        self._logger.exception("Rollback failed:")

            yield "Executed: {}".format(action)
