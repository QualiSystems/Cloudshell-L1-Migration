import os

import click

from cloudshell.layer_one.migration_tool.helpers.config_helper import ConfigHelper
from cloudshell.layer_one.migration_tool.operations.config_operations import ConfigOperations

PACKAGE_NAME = 'migration_tool'

CONFIG_PATH = os.path.join(click.get_app_dir('Quali'), PACKAGE_NAME, 'cloudshell_config.yml')


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
# @click.option(u'--gen2', 'default_view', flag_value='QQ', help="Show 2nd generation shell templates")
# @click.option(u'--gen1', 'default_view', flag_value='BB', help="Show 1st generation shell templates")
def list():
    pass

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
