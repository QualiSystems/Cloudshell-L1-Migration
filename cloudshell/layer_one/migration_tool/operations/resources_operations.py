import click

from cloudshell.layer_one.migration_tool.entities.migration_unit import MigrationUnit
from cloudshell.layer_one.migration_tool.entities.resource import Resource
from cloudshell.layer_one.migration_tool.validators.migration_units_validator import MigrationUnitsValidator


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
        migration_units = self._build_migration_units_from_arguments(old_resources, new_resources)
        validator = MigrationUnitsValidator(self._api)
        migration_units = validator.validate(migration_units)
        print(migration_units)

    def _build_migration_units_from_arguments(self, old_resources, new_resources):
        """
        :type old_resources: str
        :type new_resources: str
        """
        old_resources_list = []
        for data in old_resources.split(self.SEPARATOR):
            old_resources_list.append(Resource.from_string(data))
        new_resources_list = []
        for data in new_resources.split(self.SEPARATOR):
            new_resources_list.append(Resource.from_string(data))
        migration_units = []

        if len(new_resources_list) == 1:
            for old_resource in old_resources_list:
                migration_units.append(MigrationUnit(old_resource, new_resources_list[0]))
        elif 1 < len(new_resources_list) == len(old_resources_list):
            for old_resource, new_resource in zip(old_resources_list, new_resources_list):
                migration_units.append(MigrationUnit(old_resource, new_resource))
        else:
            raise click.UsageError('Old and New resources do not match')
        return migration_units
