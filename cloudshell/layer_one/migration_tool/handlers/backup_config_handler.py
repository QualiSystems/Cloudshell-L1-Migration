import click
from cloudshell.layer_one.migration_tool.operational_entities.config_unit import ConfigUnit
from cloudshell.layer_one.migration_tool.operational_entities.resource import Resource
from cloudshell.layer_one.migration_tool.validators.config_unit_validator import ConfigUnitValidator


class BackupConfigHandler(object):
    SEPARATOR = ','
    ADDRESS_KEY = 'address'
    FAMILY_KEY = 'family'
    MODEL_KEY = 'model'

    def __init__(self, api, logger):
        """
        :type api: cloudshell.api.cloudshell_api.CloudShellAPISession
        """
        self._api = api
        self._logger = logger
        self._config_unit_validator = ConfigUnitValidator(logger)
        self.__installed_resources = {}

    def parse_backup_configuration(self, resources_str):
        """
        :type resources_str: str

        """
        backup_config_list = []
        resources_conf_list = resources_str.split(self.SEPARATOR)
        for index in xrange(len(resources_conf_list)):
            backup_config_list.append(ConfigUnit(resources_conf_list[index]))
        return backup_config_list

    @property
    def _installed_resources(self):
        if not self.__installed_resources:
            for resource in self._api.GetResourceList().Resources:
                name = resource.Name
                address = resource.Address
                resource_family = resource.ResourceFamilyName
                resource_model = resource.ResourceModelName
                self.__installed_resources[name] = {self.FAMILY_KEY: resource_family, self.MODEL_KEY: resource_model,
                                                    self.ADDRESS_KEY: address}
        return self.__installed_resources

    def _get_resources_by_family_model(self, family, model):
        resources_list = []
        for name, details in self._installed_resources.iteritems():
            resource_family = details.get(self.FAMILY_KEY)
            resource_model = details.get(self.MODEL_KEY)
            if family == resource_family and model == resource_model:
                resources_list.append(name)
        return resources_list

    def define_backup_resources(self, backup_config):
        """
        :type backup_config: cloudshell.layer_one.migration_tool.entities.config_unit.ConfigUnit
        """
        self._config_unit_validator.validate_family(backup_config)
        self._config_unit_validator.validate_model(backup_config)
        self._config_unit_validator.validate_family(backup_config)
        self._config_unit_validator.validate_model(backup_config)

        resources = []
        if backup_config.is_multi_resource():
            for resource_name in self._get_resources_by_family_model(backup_config.resource_family,
                                                                     backup_config.resource_model):
                resources.append(self._create_resource(resource_name))
        else:
            resources.append(self._create_resource(backup_config.resource_name))
        return resources

    def _create_resource(self, resource_name):

        if not resource_name:
            raise Exception(self.__class__.__name__, 'Resource name is not defined')

        if resource_name in self._installed_resources:
            resource_family = self._installed_resources.get(resource_name).get(self.FAMILY_KEY)
            resource_model = self._installed_resources.get(resource_name).get(self.MODEL_KEY)
            address = self._installed_resources.get(resource_name).get(self.ADDRESS_KEY)

            return Resource(resource_name, address=address, family=resource_family, model=resource_model, exist=True)
        else:
            raise click.ClickException('Resource {} does not exist'.format(resource_name))
