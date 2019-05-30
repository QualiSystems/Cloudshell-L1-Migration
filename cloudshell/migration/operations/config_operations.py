import base64
import binascii
import os
from copy import deepcopy
from platform import node

import click
import yaml
from backports.functools_lru_cache import lru_cache


class ConfigOperations(object):
    PACKAGE_NAME = 'migration_tool'
    CONFIG_PATH = os.path.join(click.get_app_dir('Quali'), PACKAGE_NAME, 'cloudshell_config.yml')
    BACKUP_LOCATION = os.path.join(click.get_app_dir('Quali'), PACKAGE_NAME, 'Backup')
    LOG_PATH = os.path.join(click.get_app_dir('Quali'), PACKAGE_NAME, 'Log')
    PORT_FAMILIES = ['L1 Switch Port', 'Port', 'CS_Port']
    L1_FAMILIES = ['L1 Switch']

    class KEY:
        # Basic
        USERNAME = 'username'
        PASSWORD = 'password'
        DOMAIN = 'domain'
        HOST = 'host'
        PORT = 'port'
        LOG_LEVEL = 'log_level'
        LOG_PATH = 'log_path'
        NEW_RESOURCE_NAME_PREFIX = 'name_prefix'
        BACKUP_LOCATION = 'backup_location'
        # Associations
        PATTERN = 'pattern'
        ASSOCIATE_BY_ADDRESS = 'by_address'
        ASSOCIATE_BY_NAME = 'by_name'
        ASSOCIATE_BY_PORT_NAME = 'by_port_name'

    ASSOCIATIONS_TABLE = {
        '*/*': {KEY.PATTERN: r'.*/CH(.*)/M(.*)/SM(.*)/P(.*)', KEY.ASSOCIATE_BY_ADDRESS: True,
                KEY.ASSOCIATE_BY_NAME: True,
                KEY.ASSOCIATE_BY_PORT_NAME: True},
        'L1 Switch/*': {KEY.PATTERN: r'.*/(.*)/(.*)', KEY.ASSOCIATE_BY_ADDRESS: True, KEY.ASSOCIATE_BY_NAME: True,
                                     KEY.ASSOCIATE_BY_PORT_NAME: True},
        'L1 Switch/OS-192': {KEY.PATTERN: r'.*/.*/(.*)/(.*)', KEY.ASSOCIATE_BY_ADDRESS: True},
        'Switch/Arista EOS Switch': {KEY.PATTERN: r'.*/.*/(.*)/(.*)', KEY.ASSOCIATE_BY_ADDRESS: True,
                                     KEY.ASSOCIATE_BY_NAME: True,
                                     KEY.ASSOCIATE_BY_PORT_NAME: True},
        'Router/Arista EOS Router': {KEY.PATTERN: r'.*/.*/(.*)/(.*)', KEY.ASSOCIATE_BY_ADDRESS: True,
                                     KEY.ASSOCIATE_BY_NAME: True,
                                     KEY.ASSOCIATE_BY_PORT_NAME: True},
        'CS_Router/AristaEosRouterShell2G': {KEY.PATTERN: r'.*/.*/M(.*)/P(.*)', KEY.ASSOCIATE_BY_ADDRESS: True,
                                             KEY.ASSOCIATE_BY_NAME: True,
                                             KEY.ASSOCIATE_BY_PORT_NAME: True},
        'CS_Switch/AristaEosSwitchShell2G': {KEY.PATTERN: r'.*/.*/M(.*)/P(.*)', KEY.ASSOCIATE_BY_ADDRESS: True,
                                             KEY.ASSOCIATE_BY_NAME: True,
                                             KEY.ASSOCIATE_BY_PORT_NAME: True}
    }

    L1_ATTRIBUTES = [
        'User', 'Password']

    SHELL_ATTRIBUTES = ['User', 'Password', 'Enable Password', 'CLI Connection Type', 'SNMP Read Community',
                        'SNMP Version', 'Enable SNMP', 'Disable SNMP', 'Console Password', 'Console Port',
                        'Console Server IP Address', 'Console User', 'Power Management', 'Sessions Concurrency Limit',
                        'SNMP Write Community', 'VRF Management Name']

    DEFAULT_CONFIGURATION = {
        KEY.USERNAME: 'admin',
        KEY.DOMAIN: 'Global',
        KEY.PASSWORD: 'admin',
        KEY.HOST: 'localhost',
        KEY.PORT: 8029,
        KEY.LOG_PATH: LOG_PATH,
        KEY.LOG_LEVEL: 'DEBUG',
        KEY.NEW_RESOURCE_NAME_PREFIX: 'new_',
        KEY.BACKUP_LOCATION: BACKUP_LOCATION,
        # ASSOCIATIONS_TABLE_KEY: ASSOCIATIONS_TABLE,
    }

    def __init__(self, config_path):
        self._config_path = config_path or self.CONFIG_PATH

    @property
    @lru_cache()
    def configuration(self):
        return self._read_configuration()

    @property
    def _associations_table(self):
        return self.ASSOCIATIONS_TABLE

    def save(self):
        self._write_configuration(self.configuration)

    @staticmethod
    def _config_path_is_ok(config_path):
        if config_path and os.path.isfile(config_path) and os.access(config_path, os.R_OK):
            return True
        return False

    def _read_configuration(self):
        """Read configuration from file if exists or use default"""
        if ConfigOperations._config_path_is_ok(self._config_path):
            with open(self._config_path, 'r') as config:
                configuration = yaml.load(config)
                if configuration:
                    configuration = PasswordModification.decrypt_password(configuration)
                    # if self._update_configuration(configuration) | self._update_associations_table(configuration):
                    # if self._update_configuration(configuration):
                    #     self._write_configuration(configuration)
                else:
                    configuration = self.DEFAULT_CONFIGURATION

        else:
            configuration = self.DEFAULT_CONFIGURATION
        return configuration

    def _update_configuration(self, configuration):
        updated = False
        for key, value in self.DEFAULT_CONFIGURATION.iteritems():
            if key not in configuration:
                configuration[key] = value
                updated = True
        return updated

    # def _update_associations_table(self, configuration):
    #     updated = False
    #     associations_table = configuration.get(self.ASSOCIATIONS_TABLE_KEY)
    #     for key, value in self.DEFAULT_CONFIGURATION.get(self.ASSOCIATIONS_TABLE_KEY).items():
    #         if key not in associations_table:
    #             associations_table[key] = value
    #             updated = True
    #     return updated

    def get_association_configuration(self, family, model):
        """
        :param str family:
        :param str model:
        :rtype: dict
        """
        key_order = ['{}/{}'.format(family, model), '{}/*'.format(family), '*/*']
        for key in key_order:
            association_conf = self._associations_table.get(key)
            if association_conf:
                return association_conf

    def _write_configuration(self, configuration):
        if not ConfigOperations._config_path_is_ok(self._config_path):
            try:
                os.makedirs(os.path.dirname(self._config_path))
            except OSError:
                pass
        with open(self._config_path, 'w') as config_file:
            configuration = PasswordModification.encrypt_password(deepcopy(configuration))
            yaml.dump(configuration, config_file, default_flow_style=False)

    def read_key(self, complex_key, default_value=None):
        """
        Value for complex key like CLI.PORTS
        :param complex_key:
        :param default_value: Default value
        :return:
        """
        value = self.configuration
        for key in complex_key.split('.'):
            if isinstance(value, dict):
                value = value.get(key)
            else:
                value = None
                break

        return value or default_value

    def read_key_or_default(self, key):
        return self.read_key(key, self.DEFAULT_CONFIGURATION.get(key))


class PasswordModification(object):

    @staticmethod
    def encrypt_password(data):
        """
        Encrypt password
        :type data: dict
        """
        value = data.get(ConfigOperations.KEY.PASSWORD)
        encryption_key = PasswordModification._get_encryption_key()
        encoded = PasswordModification._decode_encode(value, encryption_key)
        data[ConfigOperations.KEY.PASSWORD] = base64.b64encode(encoded)
        return data

    @staticmethod
    def decrypt_password(data):
        value = data.get(ConfigOperations.KEY.PASSWORD)
        try:
            encryption_key = PasswordModification._get_encryption_key()
            decoded = PasswordModification._decode_encode(base64.decodestring(value), encryption_key)
            data[ConfigOperations.KEY.PASSWORD] = decoded
        except binascii.Error:
            data[ConfigOperations.KEY.PASSWORD] = value
        return data

    @staticmethod
    def _get_encryption_key():
        machine_name = node()
        if not machine_name:
            raise Exception(PasswordModification.__class__.__name__, 'Cannot get encryption key')
        return machine_name

    @staticmethod
    def _decode_encode(value, key):
        return ''.join(chr(ord(source) ^ ord(key)) for source, key in zip(value, key * 100))
