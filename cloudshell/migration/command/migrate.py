import click
from backports.functools_lru_cache import lru_cache

from cloudshell.logging.utils.error_handling_context_manager import ErrorHandlingContextManager
from cloudshell.migration.action.core import ActionsContainer
from cloudshell.migration.action.initializers import ConnectionInitializer, L1RouteInitializer, RouteInitializer, \
    ConnectorInitializer, BlueprintInitializer
from cloudshell.migration.command.core import Command


class MigrateFlow(Command):
    _ACTION_INITIALIZERS = [ConnectionInitializer, L1RouteInitializer, RouteInitializer, ConnectorInitializer,
                            BlueprintInitializer]

    def __init__(self, core_factory, operation_factory, configuration, resource_builder, associator):
        """

        :param cloudshell.migration.factory.CoreFactory core_factory:
        :param cloudshell.migration.core.operations.factory.OperationsFactory operation_factory:
        :param cloudshell.migration.configuration.config.Configuration configuration:
        :param cloudshell.migration.resource.resourcebuilder.ResourceBuilder resource_builder:
        :param cloudshell.migration.association.core.Associator associator:
        """
        super(MigrateFlow, self).__init__(configuration, core_factory.logger)
        self._core_factory = core_factory
        self._operation_factory = operation_factory
        self._resource_builder = resource_builder
        self._associator = associator

    @property
    @lru_cache()
    def _action_initializers(self):
        return [init_class(self._associator, self._operation_factory, self._configuration, self._logger) for init_class
                in self._ACTION_INITIALIZERS]

    def execute_migrate_flow(self, src_resources, dst_resources, yes, override):
        with ErrorHandlingContextManager(self._logger):
            resource_pairs = self._resource_builder.define_resources_pairs_from_args(src_resources, dst_resources)

        click.echo('Resources:')
        for pair in resource_pairs:
            click.echo('{0}=>{1}'.format(*pair))

        actions_container = ActionsContainer()
        with ErrorHandlingContextManager(self._logger):
            for pair in resource_pairs:
                actions_container.append(self._initialize_actions(pair, override))

        click.echo('Next actions will be executed:')
        click.echo(actions_container.to_string())

        # if no_backup:
        #     click.echo('---- Backup will be skipped! ----')
        #
        # if dry_run:
        #     click.echo('*' * 10 + ' DRY RUN: Logical routes and connections will not be changed ' + '*' * 10)

        if not yes and not click.confirm('Do you want to continue?'):
            raise click.ClickException('Aborted.')

        with ErrorHandlingContextManager(self._logger):
            actions_container.execute_actions()

    def _initialize_actions(self, resource_pair, override):
        """
        :param cloudshell.migration.core.model.entities.ResourcesPair resource_pair:
        :return:
        """
        actions_container = ActionsContainer()
        for initializer in self._action_initializers:
            actions_container.append(initializer.initialize(resource_pair, override))
        return actions_container
