from cloudshell.migration.entities import Resource
from cloudshell.migration.operational_entities.config_unit import ConfigUnit


class ResourcesHandler(object):

    def __init__(self, api):
        self._api = api
        self.__installed_resources = None

    def show_resources(self, family):
        resources_output = '\n'.join([res.to_string() for res in self._get_installed_resources(family)])
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
            # driver = None
            resources_list.append(Resource(name, address, resource_family, model, driver, True))
        return resources_list
