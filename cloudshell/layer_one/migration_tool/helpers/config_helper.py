import base64
import binascii
import os
from copy import deepcopy
from platform import node

import yaml


class ConfigHelper(object):
    USERNAME_KEY = 'username'
    PASSWORD_KEY = 'password'
    DOMAIN_KEY = 'domain'
    HOST_KEY = 'host'
    PORT_KEY = 'port'
    LOGGING_LEVEL = 'logging_level'
    OLD_PORT_PATTERN = 'old_port_pattern'
    NEW_PORT_PATTERN = 'new_port_pattern'
    NEW_RESOURCE_NAME_PREFIX = 'name_prefix'

    DEFAULT_CONFIGURATION = {
        USERNAME_KEY: 'admin',
        DOMAIN_KEY: 'Global',
        PASSWORD_KEY: 'admin',
        HOST_KEY: 'localhost',
        PORT_KEY: 8029,
        LOGGING_LEVEL: 'DEBUG',
        OLD_PORT_PATTERN: '(.*)',
        NEW_PORT_PATTERN: '(.*)',
        NEW_RESOURCE_NAME_PREFIX: 'new_'
    }

    def __init__(self, config_path):
        self._config_path = config_path
        self._configuration = None

    @property
    def configuration(self):
        if not self._configuration:
            self._configuration = self._read_configuration()
        return self._configuration

    def save(self):
        self._write_configuration()

    @staticmethod
    def _config_path_is_ok(config_path):
        if config_path and os.path.isfile(config_path) and os.access(config_path, os.R_OK):
            return True
        return False

    def _read_configuration(self):
        """Read configuration from file if exists or use default"""
        if ConfigHelper._config_path_is_ok(self._config_path):
            with open(self._config_path, 'r') as config:
                return PasswordModification.decrypt_password(yaml.load(config))

        else:
            return self.DEFAULT_CONFIGURATION

    def _write_configuration(self):
        if not ConfigHelper._config_path_is_ok(self._config_path):
            try:
                os.makedirs(os.path.dirname(self._config_path))
            except OSError:
                pass
        with open(self._config_path, 'w') as config_file:
            configuration = PasswordModification.encrypt_password(deepcopy(self.configuration))
            yaml.dump(configuration, config_file, default_flow_style=False)

    def read_key(self, complex_key, default_value=None):
        """
        Value for complex key like CLI.PORTS
        :param complex_key:
        :param default_value: Default value
        :return:
        """
        value = self._configuration
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
