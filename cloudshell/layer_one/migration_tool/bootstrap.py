import os
import sys

import click
from cloudshell.api.cloudshell_api import CloudShellAPISession

from cloudshell.layer_one.migration_tool.commands.config_commands import ConfigCommands
from cloudshell.layer_one.migration_tool.commands.migration_commands import MigrationCommands
from cloudshell.layer_one.migration_tool.commands.resources_commands import ResourcesCommands
from cloudshell.layer_one.migration_tool.handlers.logical_routes_handler import LogicalRoutesHandler
from cloudshell.layer_one.migration_tool.helpers.config_helper import ConfigHelper
from cloudshell.layer_one.migration_tool.helpers.logger import Logger
from cloudshell.layer_one.migration_tool.helpers.output_formater import OutputFormatter

PACKAGE_NAME = 'migration_tool'

CONFIG_PATH = os.path.join(click.get_app_dir('Quali'), PACKAGE_NAME, 'cloudshell_config.yml')

L1_FAMILY = 'L1 Switch'

DRY_RUN = False


@click.group()
def cli():
    pass


@cli.command()
@click.argument(u'key', type=str, default=None, required=False)
@click.argument(u'value', type=str, default=None, required=False)
@click.option(u'--config', 'config_path', default=CONFIG_PATH, help="Configuration file.")
def config(key, value, config_path):
    """
    Configuration
    """
    config_operations = ConfigCommands(ConfigHelper(config_path))
    if key and value:
        config_operations.set_key_value(key, value)
    elif key:
        click.echo(config_operations.get_key_value(key))
    else:
        click.echo(config_operations.get_config_description())


@cli.command()
@click.option(u'--config', 'config_path', default=CONFIG_PATH, help="Configuration file.")
@click.option(u'--family', 'family', default=L1_FAMILY, help="Resource Family.")
def show_resources(config_path, family):
    config_helper = ConfigHelper(config_path)
    api = _initialize_api(config_helper.configuration)
    resources_operations = ResourcesCommands(api)
    click.echo(resources_operations.show_resources(family))


@cli.command()
@click.option(u'--config', 'config_path', default=CONFIG_PATH, help="Configuration file.")
@click.option(u'--dry-run/--run', 'dry_run', default=False, help="Dry run.")
@click.argument(u'src_resources', type=str, default=None, required=True)
@click.argument(u'dst_resources', type=str, default=None, required=True)
def migrate(config_path, dry_run, src_resources, dst_resources):
    config_helper = ConfigHelper(config_path)
    api = _initialize_api(config_helper.configuration)
    logger = _initialize_logger(config_helper.configuration)
    migration_commands = MigrationCommands(api, logger, config_helper.configuration, dry_run)
    migration_configs = migration_commands.prepare_configs(src_resources, dst_resources)
    operations = migration_commands.prepare_operations(migration_configs)
    logical_routes_handler = LogicalRoutesHandler(api, logger, dry_run)
    logical_routes = logical_routes_handler.get_logical_routes(operations)
    operations_is_valid = len([operation for operation in operations if operation.valid]) > 0
    if not operations_is_valid:
        click.echo('No valid operations:')
        click.echo(OutputFormatter.format_prepared_invalid_operations(operations))
        sys.exit(1)

    click.echo('Following operations will be performed:')
    click.echo(OutputFormatter.format_prepared_valid_operations(operations))
    click.echo('Following operations will be ignored:')
    click.echo(OutputFormatter.format_prepared_invalid_operations(operations))
    click.echo('Following routes will be reconnected:')
    click.echo(OutputFormatter.format_logical_routes(logical_routes))

    if dry_run:
        click.echo('*' * 10 + ' DRY RUN: Logical routes and connections will not be changed ' + '*' * 10)

    if not click.confirm('Do you want to continue?'):
        click.echo('Aborted')
        sys.exit(1)

    logger.debug('Disconnecting logical routes:')
    logical_routes_handler.remove_logical_routes(logical_routes)
    logger.debug('Performing operations:')
    migration_commands.perform_operations(operations)
    logger.debug('Connecting logical routes:')
    logical_routes_handler.create_logical_routes(logical_routes)

@cli.command()
@click.option(u'--config', 'config_path', default=CONFIG_PATH, help="Configuration file.")
@click.option(u'--dry-run/--run', 'dry_run', default=False, help="Dry run.")
@click.argument(u'resources', type=str, default=None, required=True)
def backup(config_path, dry_run, resources):
    config_helper = ConfigHelper(config_path)
    api = _initialize_api(config_helper.configuration)
    logger = _initialize_logger(config_helper.configuration)


def _initialize_api(configuration):
    """
    :type configuration: dict
    """
    return CloudShellAPISession(configuration.get(ConfigHelper.HOST_KEY),
                                configuration.get(ConfigHelper.USERNAME_KEY),
                                configuration.get(ConfigHelper.PASSWORD_KEY),
                                configuration.get(ConfigHelper.DOMAIN_KEY),
                                port=configuration.get(ConfigHelper.PORT_KEY))


def _initialize_logger(configuration):
    """
    :type configuration: dict
    """
    return Logger(configuration.get(ConfigHelper.LOGGING_LEVEL))
