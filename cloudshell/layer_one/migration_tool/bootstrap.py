import os
import sys

import click

from cloudshell.api.cloudshell_api import CloudShellAPISession
from cloudshell.layer_one.migration_tool.commands.backup_commands import BackupCommands
from cloudshell.layer_one.migration_tool.commands.config_commands import ConfigCommands
from cloudshell.layer_one.migration_tool.commands.migration_commands import MigrationCommands
from cloudshell.layer_one.migration_tool.commands.resources_commands import ResourcesCommands
from cloudshell.layer_one.migration_tool.commands.restore_commands import RestoreCommands
from cloudshell.layer_one.migration_tool.helpers.config_helper import ConfigHelper
from cloudshell.layer_one.migration_tool.helpers.logger import Logger
from cloudshell.layer_one.migration_tool.helpers.output_formater import OutputFormatter

L1_FAMILY = 'L1 Switch'

DRY_RUN = False


@click.group()
def cli():
    pass


@cli.command()
@click.argument(u'key', type=str, default=None, required=False)
@click.argument(u'value', type=str, default=None, required=False)
@click.option(u'--config', 'config_path', default=None, help="Configuration file.")
@click.option(u'--patterns_table', is_flag=True, default=False, help='Add key:value to patterns table')
def config(key, value, config_path, patterns_table):
    """
    Configuration
    """
    config_operations = ConfigCommands(ConfigHelper(config_path))

    if patterns_table:
        if key and value:
            config_operations.set_patterns_table_value(key, value)
        elif key:
            click.echo(config_operations.get_patterns_table_value(key))
        else:
            click.echo('Patterns Table:')
            click.echo(config_operations.get_patterns_table_description())
    else:
        if key and value:
            config_operations.set_key_value(key, value)
        elif key:
            click.echo(config_operations.get_key_value(key))
        else:
            click.echo(config_operations.get_config_description())


@cli.command()
@click.option(u'--config', 'config_path', default=None, help="Configuration file.")
@click.option(u'--family', 'family', default=L1_FAMILY, help="Resource Family.")
def show_resources(config_path, family):
    config_helper = ConfigHelper(config_path)
    api = _initialize_api(config_helper.configuration)
    resources_operations = ResourcesCommands(api)
    click.echo(resources_operations.show_resources(family))


# @cli.command()
# @click.option(u'--config', 'config_path', default=None, help="Configuration file.")
# @click.option(u'--dry-run/--run', 'dry_run', default=False, help="Dry run.")
# @click.argument(u'src_resources', type=str, default=None, required=True)
# @click.argument(u'dst_resources', type=str, default=None, required=True)
# def migrate(config_path, dry_run, src_resources, dst_resources):
#     config_helper = ConfigHelper(config_path)
#     api = _initialize_api(config_helper.configuration)
#     logger = _initialize_logger(config_helper.configuration)
#     migration_commands = MigrationCommands(api, logger, config_helper.configuration, dry_run)
#     migration_configs = migration_commands.prepare_configs(src_resources, dst_resources)
#     operations = migration_commands.prepare_operations(migration_configs)
#     logical_routes_handler = LogicalRoutesHandler(api, logger, dry_run)
#     logical_routes = logical_routes_handler.get_logical_routes(operations)
#     operations_is_valid = len([operation for operation in operations if operation.valid]) > 0
#     if not operations_is_valid:
#         click.echo('No valid operations:')
#         click.echo(OutputFormatter.format_prepared_invalid_operations(operations))
#         sys.exit(1)
#
#     click.echo('Following operations will be performed:')
#     click.echo(OutputFormatter.format_prepared_valid_operations(operations))
#     click.echo('Following operations will be ignored:')
#     click.echo(OutputFormatter.format_prepared_invalid_operations(operations))
#     click.echo('Following routes will be reconnected:')
#     click.echo(OutputFormatter.format_logical_routes(logical_routes))
#
#     if dry_run:
#         click.echo('*' * 10 + ' DRY RUN: Logical routes and connections will not be changed ' + '*' * 10)
#
#     if not click.confirm('Do you want to continue?'):
#         click.echo('Aborted')
#         sys.exit(1)
#
#     logger.debug('Disconnecting logical routes:')
#     logical_routes_handler.remove_logical_routes(logical_routes)
#     logger.debug('Performing operations:')
#     migration_commands.perform_operations(operations)
#     logger.debug('Connecting logical routes:')
#     logical_routes_handler.create_logical_routes(logical_routes)

@cli.command()
@click.option(u'--config', 'config_path', default=None, help="Configuration file.")
@click.option(u'--dry-run/--run', 'dry_run', default=False, help="Dry run.")
@click.option(u'--backup_file', default=None, help="Backup file path.")
@click.option(u'--yes', is_flag=True, default=False, help='Assume "yes" to all questions.')
@click.argument(u'src_resources', type=str, default=None, required=True)
@click.argument(u'dst_resources', type=str, default=None, required=True)
def migrate(config_path, dry_run, src_resources, dst_resources, yes, backup_file):
    config_helper = ConfigHelper(config_path)
    api = _initialize_api(config_helper.configuration)
    logger = _initialize_logger(config_helper.configuration)
    migrate_commands = MigrationCommands(api, logger, config_helper.configuration, dry_run)
    resources_pairs = migrate_commands.define_resources_pairs(src_resources, dst_resources)
    # print(resources_pairs)

    click.echo('Resources to migrate:')
    for pair in resources_pairs:
        click.echo('{0}=>{1}'.format(*pair))

    if dry_run:
        click.echo('*' * 10 + ' DRY RUN: Logical routes and connections will not be changed ' + '*' * 10)

    if not yes and not click.confirm('Do you want to continue?'):
        click.echo('Aborted')
        sys.exit(1)

    actions = migrate_commands.initialize_actions(resources_pairs)
    print(actions)


@cli.command()
@click.option(u'--config', 'config_path', default=None, help="Configuration file.")
@click.option(u'--dry-run/--run', 'dry_run', default=False, help="Dry run.")
@click.option(u'--backup_file', 'backup_file', default=None, help="Backup file path.")
@click.option(u'--connections', 'connections', default=False, help="Restore connections only.")
@click.option(u'--routes', 'routes', default=False, help="Restore routes only.")
@click.option(u'--yes', is_flag=True, default=False, help='Assume "yes" to all questions.')
@click.argument(u'resources', type=str, default=None, required=True)
def backup(config_path, backup_file, dry_run, resources, connections, routes, yes):
    config_helper = ConfigHelper(config_path)

    api = _initialize_api(config_helper.configuration)
    logger = _initialize_logger(config_helper.configuration)
    backup_commands = BackupCommands(api, logger, config_helper.configuration, backup_file)
    resources = backup_commands.initialize_resources(resources)

    click.echo('Resources to backup:')
    for resource in resources:
        click.echo(resource.to_string())
    if not yes and not click.confirm('Do you want to continue?'):
        click.echo('Aborted')
        sys.exit(1)

    backup_commands.backup_resources(resources, connections, routes)
    click.echo('Backup done')


@cli.command()
@click.option(u'--config', 'config_path', default=None, help="Configuration file.")
@click.option(u'--dry-run/--run', 'dry_run', default=False, help="Dry run.")
@click.option(u'--file', 'backup_file', default=None, help="Backup file path.")
@click.option(u'--override', is_flag=True, default=False, help="Append or override routes/connections.")
@click.option(u'--yes', is_flag=True, default=False, help='Assume "yes" to all questions.')
@click.option(u'--connections', 'connections', default=False, help="Restore connections only.")
@click.option(u'--routes', 'routes', default=False, help="Restore routes only.")
@click.argument(u'resources', type=str, default=None, required=True)
def restore(config_path, backup_file, dry_run, resources, connections, routes, override, yes):
    config_helper = ConfigHelper(config_path)
    api = _initialize_api(config_helper.configuration)
    logger = _initialize_logger(config_helper.configuration)
    restore_commands = RestoreCommands(api, logger, config_helper.configuration, backup_file)
    resources = restore_commands.initialize_resources(resources)
    actions_container = restore_commands.define_actions(resources, connections, routes, override)

    if actions_container.is_empty():
        click.echo('Nothing to do')
        sys.exit(0)
    click.echo('Actions:')
    click.echo(actions_container.to_string())
    if not yes and not click.confirm('Do you want to continue?'):
        click.echo('Aborted')
        sys.exit(1)
    actions_container.execute_actions()


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
    return Logger(configuration.get(ConfigHelper.LOGGING_LEVEL_KEY))
