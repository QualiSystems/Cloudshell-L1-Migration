from abc import ABCMeta


class Action(object):
    __metaclass__ = ABCMeta

    def execute(self):
        pass

class RemoveRouteAction(Action):

    def __init__(self):