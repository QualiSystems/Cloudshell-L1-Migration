from cloudshell.layer_one.migration_tool.entities.config_unit import ConfigUnit
from cloudshell.layer_one.migration_tool.entities.resource import Resource


class ResourcesCommands(object):

    def __init__(self, api):
        self._api = api
        self.__installed_resources = None

    def show_resources(self, family):
        resources_output = '\n'.join([res.description() for res in self._get_installed_resources(family)])
        return ConfigUnit.FORMAT + '\n' + resources_output

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
