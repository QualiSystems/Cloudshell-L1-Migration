import sys

import click
import pkg_resources

from cloudshell.api.cloudshell_api import CloudShellAPISession
from cloudshell.layer_one.migration_tool.command_handlers.backup_handler import BackupHandler
from cloudshell.layer_one.migration_tool.command_handlers.configuration_handler import ConfigurationHandler
from cloudshell.layer_one.migration_tool.command_handlers.migration_handler import MigrationHandler
from cloudshell.layer_one.migration_tool.command_handlers.resources_handler import ResourcesHandler
from cloudshell.layer_one.migration_tool.command_handlers.restore_handler import RestoreHandler
from cloudshell.layer_one.migration_tool.helpers.config_helper import ConfigHelper
from cloudshell.layer_one.migration_tool.helpers.logger import Logger, ExceptionLogger
from cloudshell.layer_one.migration_tool.operations.logical_route_operations import LogicalRouteOperations
from cloudshell.layer_one.migration_tool.operations.resource_operations import ResourceOperations

L1_FAMILY = 'L1 Switch'

DRY_RUN = False


@click.group(invoke_without_command=True)
@click.option(u'--version', is_flag=True, default=False, help='Package version.')
@click.pass_context
def cli(ctx, version):
    """For more information on a specific command, type migration_tool COMMAND --help"""
    if version:
        version = pkg_resources.get_distribution(u'cloudshell-l1-migration').version
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
    configuration_handler = ConfigurationHandler(ConfigHelper(config_path))

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
@click.option(u'--family', 'family', default=L1_FAMILY, help="Show resources of a particular Family.")
def show(config_path, family):
    """
    Show L1 resources.
    """
    config_helper = ConfigHelper(config_path)
    api = _initialize_api(config_helper)
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
    config_helper = ConfigHelper(config_path)
    api = _initialize_api(config_helper)
    logger = _initialize_logger(config_helper)
    resource_operations = ResourceOperations(api, logger, config_helper, dry_run)
    logical_route_operations = LogicalRouteOperations(api, logger, dry_run)
    migration_handler = MigrationHandler(api, logger, config_helper, resource_operations,
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
        backup_handler = BackupHandler(api, logger, config_helper.configuration, backup_file, resource_operations,
                                       logical_route_operations)
        with ExceptionLogger(logger):
            backup_handler.backup_resources([src for src, dst in resources_pairs])

    with ExceptionLogger(logger):
        actions_container.execute_actions()


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
    config_helper = ConfigHelper(config_path)

    api = _initialize_api(config_helper)
    logger = _initialize_logger(config_helper)
    resource_operations = ResourceOperations(api, logger, config_helper)
    logical_route_operations = LogicalRouteOperations(api, logger)
    backup_handler = BackupHandler(api, logger, config_helper.configuration, backup_file, resource_operations,
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
        backup_handler.backup_resources(resources, connections, routes)
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
    config_helper = ConfigHelper(config_path)
    api = _initialize_api(config_helper)
    logger = _initialize_logger(config_helper)
    resource_operations = ResourceOperations(api, logger, config_helper, dry_run)
    logical_route_operations = LogicalRouteOperations(api, logger, dry_run)
    restore_handler = RestoreHandler(api, logger, config_helper.configuration, backup_file, resource_operations,
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
        actions_container.execute_actions()


def _initialize_api(config_helper):
    """
    :type config_helper: cloudshell.layer_one.migration_tool.helpers.config_helper.ConfigHelper
    """
    try:
        return CloudShellAPISession(config_helper.read_key(config_helper.HOST_KEY,
                                                           config_helper.DEFAULT_CONFIGURATION.get(
                                                               config_helper.HOST_KEY)),
                                    config_helper.read_key(config_helper.USERNAME_KEY,
                                                           config_helper.DEFAULT_CONFIGURATION.get(
                                                               config_helper.USERNAME_KEY)),
                                    config_helper.read_key(config_helper.PASSWORD_KEY,
                                                           config_helper.DEFAULT_CONFIGURATION.get(
                                                               config_helper.PASSWORD_KEY)),
                                    config_helper.read_key(config_helper.DOMAIN_KEY,
                                                           config_helper.DEFAULT_CONFIGURATION.get(
                                                               config_helper.DOMAIN_KEY)),
                                    port=config_helper.read_key(config_helper.PORT_KEY,
                                                                config_helper.DEFAULT_CONFIGURATION.get(
                                                                    config_helper.PORT_KEY)))
    except IOError as e:
        click.echo('ERROR: Cannot initialize Cloudshell API connection, check API settings, details: {}'.format(e),
                   err=True)
        sys.exit(1)


def _initialize_logger(config_helper):
    """
    :type config_helper: cloudshell.layer_one.migration_tool.helpers.config_helper.ConfigHelper
    """
    return Logger(config_helper.read_key(config_helper.LOGGING_LEVEL_KEY,
                                         config_helper.DEFAULT_CONFIGURATION.get(config_helper.LOGGING_LEVEL_KEY)))
