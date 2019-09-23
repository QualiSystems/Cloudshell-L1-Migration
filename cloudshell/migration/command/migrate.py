import click
from backports.functools_lru_cache import lru_cache

from cloudshell.logging.utils.error_handling_context_manager import ErrorHandlingContextManager
from cloudshell.migration.action.blueprint import UpdateBlueprintAction
from cloudshell.migration.action.connection import UpdateConnectionAction
from cloudshell.migration.action.connector import UpdateConnectorAction
from cloudshell.migration.action.core import ActionsContainer, ActionExecutor

from cloudshell.migration.action.logical_route import UpdateL1RouteAction, UpdateRouteAction
from cloudshell.migration.association.associator import Associator
from cloudshell.migration.command.core import Command
from cloudshell.migration.exceptions import AssociationException


class MigrateFlow(Command):
    REGISTERED_ACTIONS = [UpdateConnectionAction, UpdateL1RouteAction, UpdateRouteAction, UpdateConnectorAction,
                          UpdateBlueprintAction]

    def __init__(self, core_factory, operation_factory, configuration, resource_builder):
        """

        :param cloudshell.migration.factory.CoreFactory core_factory:
        :param cloudshell.migration.core.operations.factory.OperationsFactory operation_factory:
        :param cloudshell.migration.configuration.config.Configuration configuration:
        :param cloudshell.migration.resource.resourcebuilder.ResourceBuilder resource_builder:
        """
        super(MigrateFlow, self).__init__(configuration, core_factory.logger)
        self._core_factory = core_factory
        self._operation_factory = operation_factory
        self._resource_builder = resource_builder

    def _initialize_actions(self, resource_pair, override):
        action_container = ActionsContainer()
        for action_class in self.REGISTERED_ACTIONS:
            actions = action_class.initialize_for_pair(resource_pair, override,
                                                       resource_pair.associator.global_association_table,
                                                       self._operation_factory, self._logger)
            action_container.extend(actions)
        return action_container

    def execute_migrate_flow(self, src_resources, dst_resources, yes, override):
        with ErrorHandlingContextManager(self._logger):
            resource_pairs = self._resource_builder.define_resources_pairs_from_args(src_resources, dst_resources)

        click.echo('Resources:')
        for pair in resource_pairs:
            click.echo('{0}=>{1}'.format(pair.src_resource, pair.dst_resource))

        actions_container = ActionsContainer()
        with ErrorHandlingContextManager(self._logger):
            for pair in resource_pairs:
                pair.associator = Associator(pair, self._configuration, self._logger)
                if not pair.associator.valid():
                    raise AssociationException('Cannot associate {}'.format(str(resource_pairs)))
                actions_container.extend(self._initialize_actions(pair, override))

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
            actions_executor = ActionExecutor(self._logger)
            for execution_result in actions_executor.iter_execution(actions_container):
                click.echo(execution_result)
