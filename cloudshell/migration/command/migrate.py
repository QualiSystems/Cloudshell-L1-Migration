from cloudshell.migration.command.core import Command


class Migrate(Command):
    def __init__(self, core_factory, operation_factory, configuration, logger):
        super(Migrate, self).__init__(configuration, logger)
        self.core_factory = core_factory
        self.operation_factory = operation_factory



