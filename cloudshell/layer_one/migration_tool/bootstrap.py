import os

import click
from cloudshell.api.cloudshell_api import CloudShellAPISession

from cloudshell.layer_one.migration_tool.helpers.config_helper import ConfigHelper
from cloudshell.layer_one.migration_tool.operations.config_operations import ConfigOperations
from cloudshell.layer_one.migration_tool.operations.resources_operations import ResourcesOperations

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
    config_operations = ConfigOperations(ConfigHelper(config_path))
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
    resources_operations = ResourcesOperations(api)
    click.echo(resources_operations.show_resources(family))


@cli.command()
@click.option(u'--config', 'config_path', default=CONFIG_PATH, help="Configuration file")
@click.argument(u'old_resources', type=str, default=None, required=False)
@click.argument(u'new_resources', type=str, default=None, required=False)
def migrate(config_path, old_resources, new_resources):
    config_helper = ConfigHelper(config_path)
    api = _initialize_api(config_helper.configuration)
    resources_operations = ResourcesOperations(api)
    resources_operations.migrate_resources(old_resources, new_resources)


def _initialize_api(configuration):
    """
    :type configuration: dict
    """
    return CloudShellAPISession(configuration.get(ConfigHelper.HOST_KEY),
                                configuration.get(ConfigHelper.USERNAME_KEY),
                                configuration.get(ConfigHelper.PASSWORD_KEY),
                                configuration.get(ConfigHelper.DOMAIN_KEY),
                                port=configuration.get(ConfigHelper.PORT_KEY))

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
