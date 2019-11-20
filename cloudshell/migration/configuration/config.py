import base64
import binascii
import os
import shutil
from copy import deepcopy
from platform import node

import click
import yaml
from backports.functools_lru_cache import lru_cache

from cloudshell.migration.core.model.entities import AssociateItem


class ConfigAttribute(object):
    def __init__(self, key, default_value=None):
        self._key = key
        self._default_value = default_value

    def __get__(self, instance, owner):
        """
        :param Configuration instance:
        :param owner:
        :return:
        """
        if instance is None:
            return self

        return instance.read_key(self._key, self._default_value)

    # def __set__(self, instance, value):
    #     """
    #     :param Configuration instance:
    #     :param value:
    #     :return:
    #     """
    #     pass


class Configuration(object):
    PACKAGE_NAME = u'cloudshell-migration'
    # PACKAGE_NAME = 'migration_tool'
    APP_PATH = os.path.join(click.get_app_dir('Quali'), PACKAGE_NAME)
    CONFIG_PATH = os.path.join(APP_PATH, 'cloudshell_config.yml')
    ASSOCIATIONS_PATH = str(os.path.join(APP_PATH, 'associations_table.yml'))
    ASSOCIATIONS_TEMPLATE_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'association',
                                              'associations_table_template.yaml')
    BACKUP_LOCATION = os.path.join(APP_PATH, 'Backup')
    LOG_PATH = str(os.path.join(APP_PATH, 'Logs'))
    # PORT_FAMILIES = ['L1 Switch Port', 'Port', 'CS_Port']
    L1_FAMILIES = ['L1 Switch', 'L1 Robotic Switch']

    L1_ATTRIBUTES = [
        'User', 'Password']

    SHELL_ATTRIBUTES = ['User', 'Password', 'Enable Password', 'CLI Connection Type', 'SNMP Read Community',
                        'SNMP Version', 'Enable SNMP', 'Disable SNMP', 'Console Password', 'Console Port',
                        'Console Server IP Address', 'Console User', 'Power Management', 'Sessions Concurrency Limit',
                        'SNMP Write Community', 'VRF Management Name']

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
        ASSOCIATION_TABLE_PATH = 'associations_table_path'

        # Associations
        FAMILY = 'family'
        MODEL = 'model'
        ADDRESS_PATTERN = 'address_pattern'
        NAME_PATTERN = 'name_pattern'

    DEFAULT_VALUES = {
        KEY.USERNAME: 'admin',
        KEY.DOMAIN: 'Global',
        KEY.PASSWORD: 'admin',
        KEY.HOST: 'localhost',
        KEY.PORT: 8029,
        KEY.LOG_PATH: LOG_PATH,
        KEY.LOG_LEVEL: 'DEBUG',
        KEY.NEW_RESOURCE_NAME_PREFIX: 'new_',
        KEY.ASSOCIATION_TABLE_PATH: ASSOCIATIONS_PATH
        # KEY.BACKUP_LOCATION: BACKUP_LOCATION,
        # ASSOCIATIONS_TABLE_KEY: ASSOCIATIONS_TABLE,
    }

    host = ConfigAttribute(KEY.HOST, DEFAULT_VALUES.get(KEY.HOST))
    username = ConfigAttribute(KEY.USERNAME, DEFAULT_VALUES.get(KEY.USERNAME))
    password = ConfigAttribute(KEY.PASSWORD, DEFAULT_VALUES.get(KEY.PASSWORD))
    domain = ConfigAttribute(KEY.DOMAIN, DEFAULT_VALUES.get(KEY.DOMAIN))
    port = ConfigAttribute(KEY.PORT, DEFAULT_VALUES.get(KEY.PORT))
    log_path = ConfigAttribute(KEY.LOG_PATH, DEFAULT_VALUES.get(KEY.LOG_PATH))
    log_level = ConfigAttribute(KEY.LOG_LEVEL, DEFAULT_VALUES.get(KEY.LOG_LEVEL))
    resource_name_prefix = ConfigAttribute(KEY.NEW_RESOURCE_NAME_PREFIX,
                                           DEFAULT_VALUES.get(KEY.NEW_RESOURCE_NAME_PREFIX))
    backup_location = ConfigAttribute(KEY.BACKUP_LOCATION, DEFAULT_VALUES.get(KEY.BACKUP_LOCATION))
    associations_table_path = ConfigAttribute(KEY.ASSOCIATION_TABLE_PATH,
                                              DEFAULT_VALUES.get(KEY.ASSOCIATION_TABLE_PATH))

    def __init__(self, config_path):
        self._config_path = config_path or self.CONFIG_PATH

    @property
    @lru_cache()
    def configuration(self):
        return self._read_configuration()

    @property
    @lru_cache()
    def _associations_table(self):
        return self._read_associations_table()

    def save(self):
        self._write_configuration(self.configuration)

    @staticmethod
    def _path_is_ok(config_path):
        if config_path and os.path.isfile(config_path) and os.access(config_path, os.R_OK):
            return True
        return False

    def _read_configuration(self):
        """Read configuration from file if exists or use default"""
        if self._path_is_ok(self._config_path):
            with open(self._config_path, 'r') as config:
                configuration = yaml.load(config)
                if configuration:
                    configuration = PasswordModification.decrypt_password(configuration)
                    # if self._update_configuration(configuration) | self._update_associations_table(configuration):
                    # if self._update_configuration(configuration):
                    #     self._write_configuration(configuration)
                else:
                    configuration = self.DEFAULT_VALUES

        else:
            configuration = self.DEFAULT_VALUES
        return configuration

    # def _update_configuration(self, configuration):
    #     updated = False
    #     for key, value in self.DEFAULT_VALUES.iteritems():
    #         if key not in configuration:
    #             configuration[key] = value
    #             updated = True
    #     return updated

    def _read_associations_table(self):
        """Read configuration from file if exists or use default"""
        if not self._path_is_ok(self.associations_table_path):
            self._initialize_association_table()

        with open(self.associations_table_path, 'r') as table_file:
            ass_table = yaml.load(table_file)
            return ass_table

    def _initialize_association_table(self):
        shutil.copy(self.ASSOCIATIONS_TEMPLATE_PATH, self.ASSOCIATIONS_PATH)

    @lru_cache()
    def get_association_configuration(self, item):
        """
        :param cloudshell.migration.core.model.entities.AssociateItem item:
        :rtype: dict
        """
        family = item.family
        model = item.model
        key_order = ['{}/{}'.format(family, model), '{}/*'.format(family), '*/*']
        for key in key_order:
            association_conf = self._associations_table.get(key)
            if association_conf:
                return association_conf

    def get_association_families(self, item):
        """
        :param cloudshell.migration.core.model.entities.AssociateItem item:
        :return:
        """
        result = set()
        for conf in self.get_association_configuration(item).values():
            families = conf.get(self.KEY.FAMILY)
            if families:
                result.update(families)
        return result

    def _write_configuration(self, configuration):
        if not self._path_is_ok(self._config_path):
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
        return self.read_key(key, self.DEFAULT_VALUES.get(key))


class PasswordModification(object):

    @staticmethod
    def encrypt_password(data):
        """
        Encrypt password
        :type data: dict
        """
        value = data.get(Configuration.KEY.PASSWORD)
        encryption_key = PasswordModification._get_encryption_key()
        encoded = PasswordModification._decode_encode(value, encryption_key)
        data[Configuration.KEY.PASSWORD] = base64.b64encode(encoded)
        return data

    @staticmethod
    def decrypt_password(data):
        value = data.get(Configuration.KEY.PASSWORD)
        try:
            encryption_key = PasswordModification._get_encryption_key()
            decoded = PasswordModification._decode_encode(base64.decodestring(value), encryption_key)
            data[Configuration.KEY.PASSWORD] = decoded
        except binascii.Error:
            data[Configuration.KEY.PASSWORD] = value
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
