import base64
import binascii
import os
from copy import deepcopy
from platform import node

import click
import yaml
from backports.functools_lru_cache import lru_cache


class ConfigHelper(object):
    PACKAGE_NAME = 'migration_tool'
    CONFIG_PATH = os.path.join(click.get_app_dir('Quali'), PACKAGE_NAME, 'cloudshell_config.yml')
    BACKUP_LOCATION = os.path.join(click.get_app_dir('Quali'), PACKAGE_NAME, 'Backup')

    USERNAME_KEY = 'username'
    PASSWORD_KEY = 'password'
    DOMAIN_KEY = 'domain'
    HOST_KEY = 'host'
    PORT_KEY = 'port'
    LOGGING_LEVEL_KEY = 'logging_level'
    NEW_RESOURCE_NAME_PREFIX_KEY = 'name_prefix'
    BACKUP_LOCATION_KEY = 'backup_location'
    PATTERN_KEY = 'pattern'
    DEFAULT_L1_PATTERN = r'.*/(.*)/(.*)'
    DEFAULT_PATTERN = r'.*/CH(.*)/M(.*)/SM(.*)/P(.*)'
    ASSOCIATE_BY_ADDRESS_KEY = 'by_address'
    ASSOCIATE_BY_NAME_KEY = 'by_name'
    ASSOCIATE_BY_PORT_NAME_KEY = 'by_port_name'
    ASSOCIATIONS_TABLE_KEY = 'associations_table'

    ASSOCIATIONS_TABLE = {
        '*/*': {PATTERN_KEY: DEFAULT_PATTERN, ASSOCIATE_BY_ADDRESS_KEY: True, ASSOCIATE_BY_NAME_KEY: True,
                ASSOCIATE_BY_PORT_NAME_KEY: True},
        'L1 Switch/*': {PATTERN_KEY: DEFAULT_L1_PATTERN, ASSOCIATE_BY_ADDRESS_KEY: True},
        'L1 Switch/OS-192': {PATTERN_KEY: r'.*/.*/(.*)/(.*)', ASSOCIATE_BY_ADDRESS_KEY: True},
        'Switch/Arista EOS Switch': {PATTERN_KEY: r'.*/.*/(.*)/(.*)', ASSOCIATE_BY_ADDRESS_KEY: True,
                                     ASSOCIATE_BY_NAME_KEY: True,
                                     ASSOCIATE_BY_PORT_NAME_KEY: True},
        'Router/Arista EOS Router': {PATTERN_KEY: r'.*/.*/(.*)/(.*)', ASSOCIATE_BY_ADDRESS_KEY: True,
                                     ASSOCIATE_BY_NAME_KEY: True,
                                     ASSOCIATE_BY_PORT_NAME_KEY: True},
        'CS_Router/AristaEosRouterShell2G': {PATTERN_KEY: r'.*/.*/M(.*)/P(.*)', ASSOCIATE_BY_ADDRESS_KEY: True,
                                             ASSOCIATE_BY_NAME_KEY: True,
                                             ASSOCIATE_BY_PORT_NAME_KEY: True},
        'CS_Switch/AristaEosSwitchShell2G': {PATTERN_KEY: r'.*/.*/M(.*)/P(.*)', ASSOCIATE_BY_ADDRESS_KEY: True,
                                             ASSOCIATE_BY_NAME_KEY: True,
                                             ASSOCIATE_BY_PORT_NAME_KEY: True}
    }

    L1_ATTRIBUTES = {
        'User': 'User',
        'Password': 'Password'
    }

    SHELLS_ATTRIBUTES = {
        'User': 'User',
        'Password': 'Password'

    }

    DEFAULT_CONFIGURATION = {
        USERNAME_KEY: 'admin',
        DOMAIN_KEY: 'Global',
        PASSWORD_KEY: 'admin',
        HOST_KEY: 'localhost',
        PORT_KEY: 8029,
        LOGGING_LEVEL_KEY: 'DEBUG',
        NEW_RESOURCE_NAME_PREFIX_KEY: 'new_',
        BACKUP_LOCATION_KEY: BACKUP_LOCATION,
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
        return self.configuration.get(self.ASSOCIATIONS_TABLE_KEY)

    def save(self):
        self._write_configuration(self.configuration)

    @staticmethod
    def _config_path_is_ok(config_path):
        if config_path and os.path.isfile(config_path) and os.access(config_path, os.R_OK):
            return True
        return False

    def _read_configuration(self):
        """Read configuration from file if exists or use default"""
        if ConfigHelper._config_path_is_ok(self._config_path):
            with open(self._config_path, 'r') as config:
                configuration = yaml.load(config)
                if configuration:
                    configuration = PasswordModification.decrypt_password(configuration)
                    if self._update_configuration(configuration) | self._update_associations_table(configuration):
                        self._write_configuration(configuration)
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

    def _update_associations_table(self, configuration):
        updated = False
        associations_table = configuration.get(self.ASSOCIATIONS_TABLE_KEY)
        for key, value in self.DEFAULT_CONFIGURATION.get(self.ASSOCIATIONS_TABLE_KEY).items():
            if key not in associations_table:
                associations_table[key] = value
                updated = True
        return updated

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
        if not ConfigHelper._config_path_is_ok(self._config_path):
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


class PasswordModification(object):

    @staticmethod
    def encrypt_password(data):
        """
        Encrypt password
        :type data: dict
        """
        value = data.get(ConfigHelper.PASSWORD_KEY)
        encryption_key = PasswordModification._get_encryption_key()
        encoded = PasswordModification._decode_encode(value, encryption_key)
        data[ConfigHelper.PASSWORD_KEY] = base64.b64encode(encoded)
        return data

    @staticmethod
    def decrypt_password(data):
        value = data.get(ConfigHelper.PASSWORD_KEY)
        try:
            encryption_key = PasswordModification._get_encryption_key()
            decoded = PasswordModification._decode_encode(base64.decodestring(value), encryption_key)
            data[ConfigHelper.PASSWORD_KEY] = decoded
        except binascii.Error:
            data[ConfigHelper.PASSWORD_KEY] = value
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
