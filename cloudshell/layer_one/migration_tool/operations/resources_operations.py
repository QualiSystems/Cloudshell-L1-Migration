import click

from cloudshell.layer_one.migration_tool.entities.config_unit import ConfigUnit
from cloudshell.layer_one.migration_tool.entities.migration_config import MigrationConfig
from cloudshell.layer_one.migration_tool.entities.resource import Resource
from cloudshell.layer_one.migration_tool.handlers.migration_config_handler import MigrationConfigHandler
from cloudshell.layer_one.migration_tool.validators.migration_operation_validator import MigrationUnitValidator


class ResourcesOperations(object):
    SEPARATOR = ','

    def __init__(self, api):
        self._api = api
        self.__installed_resources = None

    def show_resources(self, family):
        resources_output = '\n'.join([res.description() for res in self._get_installed_resources(family)])
        return Resource.DESCRIPTION_HEADER + '\n' + resources_output

    def _get_installed_resources(self, family=None):
        resources_list = []
        for resource in self._api.GetResourceList().Resources:
            resource_family = resource.ResourceFamilyName
            if family and resource_family != family:
                continue
            address = resource.Address
            name = resource.Name
            model = resource.ResourceModelName
            details = self._api.GetResourceDetails(name)
            driver = details.DriverName
            resources_list.append(Resource(name, address, family, model, driver))
        return resources_list

    def migrate_resources(self, old_resources, new_resources):
        """
        :type old_resources: str
        :type new_resources: str
        """
        migration_configs = self._parse_migration_configuration(old_resources, new_resources)
        migration_config_handler = MigrationConfigHandler(self._api)
        migration_operations_list = []
        for migration_config in migration_configs:
            migration_operations_list.extend(migration_config_handler.define_operations(migration_config))
        print(migration_operations_list)

    def _parse_migration_configuration(self, old_resources_str, new_resources_str):
        """
        :type old_resources_str: str
        :type new_resources_str: str
        """
        migration_config_list = []
        old_resources_conf_list = old_resources_str.split(self.SEPARATOR)
        new_resources_conf_list = new_resources_str.split(self.SEPARATOR)

        for index in xrange(len(old_resources_conf_list)):
            if len(new_resources_conf_list) == 1:
                migration_config_list.append(
                    MigrationConfig(ConfigUnit(old_resources_conf_list[index]), ConfigUnit(new_resources_conf_list[0])))
            else:
                migration_config_list.append(
                    MigrationConfig(ConfigUnit(old_resources_conf_list[index]),
                                    ConfigUnit(new_resources_conf_list[index])))
        return migration_config_list
