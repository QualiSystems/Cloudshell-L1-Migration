from cloudshell.layer_one.migration_tool.entities.migration_operation import MigrationOperation
from cloudshell.layer_one.migration_tool.entities.resource import Resource
from cloudshell.layer_one.migration_tool.validators.config_unit_validator import ConfigUnitValidator


class MigrationConfigHandler(object):
    NEW_RESOURCE_NAME_TEMPLATE = 'new_{}'

    def __init__(self, api):
        """
        :type api: cloudshell.api.cloudshell_api.CloudShellAPISession
        """
        self._api = api
        self._config_unit_validator = ConfigUnitValidator(self._api)

    def define_operations(self, migration_config):
        """
        :type migration_config: cloudshell.layer_one.migration_tool.entities.migration_config.MigrationConfig
        """
        if migration_config.old_config.is_multi_resource():
            operations = self._define_multiple_operations(migration_config)
        else:
            operations = self._define_single_operations(migration_config)
        return operations

    def _define_multiple_operations(self, migration_config):
        """
        :type migration_config: cloudshell.layer_one.migration_tool.entities.migration_config.MigrationConfig
        """
        self._config_unit_validator.validate_family(migration_config.old_config)
        self._config_unit_validator.validate_model(migration_config.old_config)

        operations = []
        for old_resource in self._get_installed_resources(migration_config.old_config.family,
                                                          migration_config.old_config.model):
            operations.append(
                MigrationOperation(old_resource, self._build_new_resource(migration_config, old_resource),
                                   migration_config))
        return operations

    def _define_single_operations(self, migration_config):
        """
        :type migration_config: cloudshell.layer_one.migration_tool.entities.migration_config.MigrationConfig
        """
        self._config_unit_validator.validate_name(migration_config.old_config)
        old_resource = self._create_resource_by_name(migration_config.old_config.name)
        new_resource = self._build_new_resource(migration_config, old_resource)
        return [MigrationOperation(old_resource, new_resource, migration_config)]

    def _build_new_resource(self, migration_config, old_resource):
        """
        :type migration_config: cloudshell.layer_one.migration_tool.entities.migration_config.MigrationConfig
        :type old_resource: cloudshell.layer_one.migration_tool.entities.resource.Resource
        """
        if migration_config.new_config.name:
            name = migration_config.new_config.name
        else:
            name = self.NEW_RESOURCE_NAME_TEMPLATE.format(old_resource.name)

        address = old_resource.address
        self._config_unit_validator.validate_family(migration_config.new_config)
        family = migration_config.new_config.family
        self._config_unit_validator.validate_model(migration_config.new_config)
        model = migration_config.new_config.model
        driver = migration_config.new_config.driver
        return Resource(name, address, family, model, driver)

    def _get_installed_resources(self, family, model):
        resources_list = []
        for resource in self._api.GetResourceList().Resources:
            name = resource.Name
            resource_family = resource.ResourceFamilyName
            resource_model = resource.ResourceModelName
            if resource_family != family and resource_model != model:
                continue
            resources_list.append(self._create_resource_by_name(name))
        return resources_list

    def _create_resource_by_name(self, name):
        resource_details = self._api.GetResourceDetails(name)
        family = resource_details.ResourceFamilyName
        model = resource_details.ResourceModelName
        address = resource_details.Address
        driver = resource_details.DriverName
        return Resource(name, address, family, model, driver)
