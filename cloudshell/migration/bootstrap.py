#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import sys

import click
import pkg_resources

from cloudshell.api.cloudshell_api import CloudShellAPISession
from cloudshell.migration.command_handlers.backup_handler import BackupHandler
from cloudshell.migration.command_handlers.configuration_handler import ConfigurationHandler
from cloudshell.migration.command_handlers.migration_handler import MigrationHandler
from cloudshell.migration.command_handlers.resources_handler import ResourcesHandler
from cloudshell.migration.command_handlers.restore_handler import RestoreHandler
from cloudshell.migration.helpers.log_helper import ExceptionLogger
from cloudshell.migration.operations.config_operations import ConfigOperations

from cloudshell.logging.qs_logger import get_qs_logger
from cloudshell.migration.operations.logical_route_operations import LogicalRouteOperations
from cloudshell.migration.operations.resource_operations import ResourceOperations

PACKAGE_NAME = u'cloudshell-migration'


@click.group(invoke_without_command=True)
@click.option(u'--version', is_flag=True, default=False, help='Package version.')
@click.pass_context
def cli(ctx, version):
    """For more information on a specific command, type migration_tool COMMAND --help"""
    if version:
        version = pkg_resources.get_distribution(PACKAGE_NAME).version
        click.echo('Version: {}'.format(version))
        sys.exit(0)
    else:
        if not ctx.invoked_subcommand:
            click.echo(ctx.get_help())


@cli.command()
@click.argument(u'key', type=str, default=None, required=False)
@click.argument(u'value', type=str, default=None, required=False)
@click.option(u'--config', 'config_path', default=None, help="Generate a custom config file (.conf, .yaml or .yml).",
              metavar="FILE-PATH")
# @click.option(u'--associations-table', is_flag=True, default=False,
#               help='Manage ports associated table. For Quali support use only.')
def config(key, value, config_path):
    """
    Set configuration parameters.
    """
    configuration_handler = ConfigurationHandler(ConfigOperations(config_path))

    # if patterns_table:
    #     if key and value:
    #         configuration_handler.set_patterns_table_value(key, value)
    #     elif key:
    #         click.echo(configuration_handler.get_patterns_table_value(key))
    #     else:
    #         click.echo('Patterns Table(Family/Model: Pattern)')
    #         click.echo(configuration_handler.get_patterns_table_description())
    # else:
    if key and value:
        configuration_handler.set_key_value(key, value)
    elif key:
        click.echo(configuration_handler.get_key_value(key))
    else:
        click.echo(configuration_handler.get_config_description())


@cli.command()
@click.option(u'--config', 'config_path', default=None, help="Show resources based on a custom config file.",
              metavar="FILE-PATH")
@click.option(u'--family', 'family', default=None, help="Show resources of a particular Family.")
def show(config_path, family):
    """
    Show L1 resources.
    """
    config_operations = ConfigOperations(config_path)
    api = _initialize_api(config_operations)
    resources_handler = ResourcesHandler(api)
    click.echo(resources_handler.show_resources(family))


@cli.command()
@click.option(u'--config', 'config_path', default=None, help="Use a custom config file.", metavar="FILE-PATH")
@click.option(u'--dry-run', is_flag=True, default=False,
              help="Dry run creates resources but does not switch physical connections or create and remove routes.")
@click.option(u'--backup-file', default=None, help="Backup to a different yaml file.", metavar="BACKUP FILE-PATH")
@click.option(u'--yes', is_flag=True, default=False, help='Assume "yes" to all questions.')
@click.option(u'--override', is_flag=True, default=False,
              help="Port connections on the source resource override any "
                   "existing port connections on the destination resource.")
@click.option(u'--no-backup', is_flag=True, default=False,
              help='Do not create a backup file before migration.(Do not use this option. '
                   'You are advised to create a backup file before performing any migration.)')
@click.argument(u'src_resources', type=str, default=None, required=True)
@click.argument(u'dst_resources', type=str, default=None, required=True)
def migrate(config_path, dry_run, src_resources, dst_resources, yes, backup_file, no_backup, override):
    """
    Migrate connections from source (SRC) resource(s) to destination (DST) resource(s),
    for example specifying the Family/Model, or a comma-separated list of the source resources to migrate.
    For additional info - see the tool's user guide at:
    https://github.com/QualiSystems/Cloudshell-L1-Migration/blob/master/README.md.
    """
    config_operations = ConfigOperations(config_path)
    api = _initialize_api(config_operations)
    logger = _initialize_logger(config_operations)
    resource_operations = ResourceOperations(api, logger, config_operations, dry_run)
    logical_route_operations = LogicalRouteOperations(api, logger, dry_run)
    migration_handler = MigrationHandler(api, logger, config_operations, resource_operations,
                                         logical_route_operations)
    with ExceptionLogger(logger):
        resources_pairs = migration_handler.define_resources_pairs(src_resources, dst_resources)
        actions_container = migration_handler.initialize_actions(resources_pairs, override)
    # print(resources_pairs)

    click.echo('Resources:')
    for pair in resources_pairs:
        click.echo('{0}=>{1}'.format(*pair))

    click.echo('Next actions will be executed:')
    click.echo(actions_container.to_string())

    if no_backup:
        click.echo('---- Backup will be skipped! ----')

    if dry_run:
        click.echo('*' * 10 + ' DRY RUN: Logical routes and connections will not be changed ' + '*' * 10)

    if not yes and not click.confirm('Do you want to continue?'):
        click.echo('Aborted')
        sys.exit(1)

    if not no_backup and not dry_run:
        backup_handler = BackupHandler(api, logger, config_operations, backup_file, resource_operations,
                                       logical_route_operations)
        with ExceptionLogger(logger):
            backup_file = backup_handler.backup_resources([src for src, dst in resources_pairs])
            click.echo('Backup File: {}'.format(backup_file))

    with ExceptionLogger(logger):
        click.echo("Executing actions:")
        for action in actions_container.sequence():
            result = action.execute()
            click.echo(result)


@cli.command()
@click.option(u'--config', 'config_path', default=None, help="Backup using a custom yaml config file.",
              metavar="FILE-PATH")
@click.option(u'--backup-file', default=None, help="Backup to a different yaml file.", metavar="BACKUP FILE-PATH")
@click.option(u'--connections', is_flag=True, default=False, help="Backup connections only.")
@click.option(u'--routes', is_flag=True, default=False, help="Backup routes only.")
@click.option(u'--yes', is_flag=True, default=False, help='Assume "yes" to all questions.')
@click.argument(u'resources', type=str, default=None, required=False, metavar='RESOURCES')
def backup(config_path, backup_file, resources, connections, routes, yes):
    """
    Backup connections and routes.

    RESOURCES: Comma-separated list of the names of the desired resources.
    """
    config_operations = ConfigOperations(config_path)

    api = _initialize_api(config_operations)
    logger = _initialize_logger(config_operations)
    resource_operations = ResourceOperations(api, logger, config_operations)
    logical_route_operations = LogicalRouteOperations(api, logger)
    backup_handler = BackupHandler(api, logger, config_operations, backup_file, resource_operations,
                                   logical_route_operations)
    with ExceptionLogger(logger):
        resources = backup_handler.initialize_resources(resources)

    click.echo('Resources to backup:')
    for resource in resources:
        click.echo(resource.to_string())
    if not yes and not click.confirm('Do you want to continue?'):
        click.echo('Aborted')
        sys.exit(1)

    with ExceptionLogger(logger):
        backup_file = backup_handler.backup_resources(resources, connections, routes)
        click.echo('Backup File: {}'.format(backup_file))
    click.echo('Backup done')


@cli.command()
@click.option(u'--config', 'config_path', default=None, help="Use a custom config file.", metavar="FILE-PATH")
@click.option(u'--dry-run', is_flag=True, default=False, help="Dry run creates resources but does not switch "
                                                              "physical connections or create and remove routes.")
@click.option(u'--backup-file', default=None, required=True, help="Backup file path.")
@click.option(u'--override', is_flag=True, default=False, help="Port connections on the source resource override any "
                                                               "existing portconnections on the destination resource.")
@click.option(u'--yes', is_flag=True, default=False, help='Assume "yes" to all questions.')
@click.option(u'--connections', 'connections', default=False, help="Restore connections only.")
@click.option(u'--routes', 'routes', default=False, help="Restore routes only.")
@click.argument(u'resources', type=str, default=None, required=False)
def restore(config_path, backup_file, dry_run, resources, connections, routes, override, yes):
    """
    Restore connections and routes.

    BACKUP FILE-PATH:
        The full path to the backup file, including the file name.

    RESOURCES:
        Comma-separated list of the names of the desired resources.
        You do not need to specify the full path from the root of the desired resource(s).
            However, the tool will create the new resource(s) in the root.
    """
    config_operations = ConfigOperations(config_path)
    api = _initialize_api(config_operations)
    logger = _initialize_logger(config_operations)
    resource_operations = ResourceOperations(api, logger, config_operations, dry_run)
    logical_route_operations = LogicalRouteOperations(api, logger, dry_run)
    restore_handler = RestoreHandler(api, logger, config_operations, backup_file, resource_operations,
                                     logical_route_operations)
    with ExceptionLogger(logger):
        resources = restore_handler.initialize_resources(resources)
        actions_container = restore_handler.define_actions(resources, connections, routes, override)

    if actions_container.is_empty():
        click.echo('Nothing to do')
        sys.exit(0)
    click.echo('Next actions will be executed:')
    click.echo(actions_container.to_string())
    if not yes and not click.confirm('Do you want to continue?'):
        click.echo('Aborted')
        sys.exit(1)
    with ExceptionLogger(logger):
        click.echo("Executing actions:")
        for action in actions_container.sequence():
            result = action.execute()
            click.echo(result)


def _initialize_api(config_operations):
    """
    :type config_operations: cloudshell.migration.operations.config_operations.ConfigOperations
    """
    try:
        return CloudShellAPISession(config_operations.read_key_or_default(config_operations.KEY.HOST),
                                    config_operations.read_key_or_default(config_operations.KEY.USERNAME),
                                    config_operations.read_key_or_default(config_operations.KEY.PASSWORD),
                                    config_operations.read_key_or_default(config_operations.KEY.DOMAIN),
                                    port=config_operations.read_key_or_default(config_operations.KEY.PORT))
    except IOError as e:
        click.echo('ERROR: Cannot initialize Cloudshell API connection, check API settings, details: {}'.format(e),
                   err=True)
        sys.exit(1)


def _initialize_logger(config_operations):
    """
    :type config_operations: cloudshell.migration.operations.config_operations.ConfigOperations
    """

    os.environ['LOG_PATH'] = config_operations.read_key_or_default(config_operations.KEY.LOG_PATH)
    logger = get_qs_logger(str(PACKAGE_NAME), 'migration_tool', 'migration_tool')
    logger.setLevel(config_operations.read_key_or_default(config_operations.KEY.LOG_LEVEL))
    click.echo('Log file: {}'.format(logger.handlers[0].baseFilename))
    return logger
