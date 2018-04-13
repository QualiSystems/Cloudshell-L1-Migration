import os
import sys

import click
from cloudshell.api.cloudshell_api import CloudShellAPISession

from cloudshell.layer_one.migration_tool.commands.config_commands import ConfigCommands
from cloudshell.layer_one.migration_tool.commands.migration_commands import MigrationCommands
from cloudshell.layer_one.migration_tool.commands.resources_commands import ResourcesCommands
from cloudshell.layer_one.migration_tool.helpers.config_helper import ConfigHelper
from cloudshell.layer_one.migration_tool.helpers.logger import Logger
from cloudshell.layer_one.migration_tool.helpers.output_formater import OutputFormatter

PACKAGE_NAME = 'migration_tool'

CONFIG_PATH = os.path.join(click.get_app_dir('Quali'), PACKAGE_NAME, 'cloudshell_config.yml')

L1_FAMILY = 'L1 Switch'


@click.group()
def cli():
    pass


@cli.command()
@click.argument(u'key', type=str, default=None, required=False)
@click.argument(u'value', type=str, default=None, required=False)
@click.option(u'--config', 'config_path', default=CONFIG_PATH, help="Configuration file")
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
@click.option(u'--config', 'config_path', default=CONFIG_PATH, help="Configuration file")
@click.option(u'--family', 'family', default=L1_FAMILY, help="Resource Family")
def show_resources(config_path, family):
    config_helper = ConfigHelper(config_path)
    api = _initialize_api(config_helper.configuration)
    resources_operations = ResourcesCommands(api)
    click.echo(resources_operations.show_resources(family))


@cli.command()
@click.option(u'--config', 'config_path', default=CONFIG_PATH, help="Configuration file")
@click.argument(u'old_resources_str', type=str, default=None, required=False)
@click.argument(u'new_resources_str', type=str, default=None, required=False)
def migrate(config_path, old_resources_str, new_resources_str):
    print(sys.argv)
    config_helper = ConfigHelper(config_path)
    api = _initialize_api(config_helper.configuration)
    logger = _initialize_logger(config_helper.configuration)
    migration_commands = MigrationCommands(api, logger)
    migration_configs = migration_commands.prepare_configs(old_resources_str, new_resources_str)
    operations = migration_commands.prepare_operations(migration_configs)
    click.echo('The following operations will be performed:')
    click.echo(OutputFormatter.format_prepared_valid_operations(operations))
    click.echo('The following operations will be ignored:')
    click.echo(OutputFormatter.format_prepared_invalid_operations(operations))

    if not click.confirm('Do you want to continue?'):
        click.echo('Aborted')
        sys.exit(1)
    migration_commands.perform_operations(operations)
    migration_commands.reconnect_logical_routs(operations)


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

# @cli.command()
# @click.argument(u'kv', type=(str, str), default=(None, None), required=False)
# @click.option('--global/--local', 'global_cfg', default=True)
# @click.option('--remove', 'key_to_remove', default=None)
# def migrate(kv, global_cfg, key_to_remove):
#     """
#     Configures global/local config values to allow deployment over cloudshell
#     """
#     ConfigCommandExecutor(global_cfg).config(kv, key_to_remove)
#
