from cloudshell.layer_one.migration_tool.entities.connection import Connection
from cloudshell.layer_one.migration_tool.entities.port import Port


class ResourceOperationHelper(object):
    def __init__(self, api, logger):
        """
        :type api: cloudshell.api.cloudshell_api.CloudShellAPISession
        :type logger: cloudshell.layer_one.migration_tool.helpers.logger.Logger
        """
        self._api = api
        self._logger = logger
        self._resource_details_container = {}

    def _get_resource_details(self, resource):
        if resource.name not in self._resource_details_container:
            self._resource_details_container[resource.name] = self._api.GetResourceDetails(resource.name)
        return self._resource_details_container.get(resource.name)

    def define_resource_attributes(self, resource):
        """
        :type resource: cloudshell.layer_one.migration_tool.entities.resource.Resource
        """
        # resource_details = self._get_resource_details(resource)
        # if not resource.address:
        #     resource.address = resource_details.Address
        # if not resource.family:
        #     resource.family = resource_details.ResourceFamilyName
        #
        # if not resource.model:
        #     resource.model = resource_details.ResourceModelName

        for attribute in resource.attributes:
            value = self._api.GetAttributeValue(resource.name, attribute).Value
            if attribute == resource.PASSWORD_ATTRIBUTE:
                value = self._api.DecryptPassword(value).Value
            resource.attributes[attribute] = value

    def get_physical_connections(self, resource):
        """
        :type resource: cloudshell.layer_one.migration_tool.entities.resource.Resource
        """
        self._logger.debug('Getting connections for resource {}'.format(resource.name))
        # resource_details = self._get_resource_details(resource)
        resource_details = self._api.GetResourceDetails(resource.name)
        connections = self._define_connections(resource_details)
        return connections

    def _define_connections(self, resource_info):
        """
        :type resource_info: cloudshell.api.cloudshell_api.ResourceInfo
        """
        connections = {}
        if resource_info.Connections:
            connection = Connection(Port(resource_info.Name, resource_info.FullAddress),
                                    resource_info.Connections[0].FullPath,
                                    resource_info.Connections[0].Weight)
            connections[resource_info.Name] = connection
        for child_resource_info in resource_info.ChildResources:
            connections.update(self._define_connections(child_resource_info))
        return connections

    def get_resource_ports(self, resource):
        """
        :type resource: cloudshell.layer_one.migration_tool.entities.resource.Resource
        """
        self._logger.debug('Getting ports for resource {}'.format(resource.name))
        resource_details = self._get_resource_details(resource)
        ports = []
        for child_resource in resource_details.ChildResources:
            for grandchild_resource in child_resource.ChildResources:
                ports.append(Port(grandchild_resource.Name, grandchild_resource.FullAddress))
        return ports

    def create_resource(self, resource):
        """
        :type resource: cloudshell.layer_one.migration_tool.entities.resource.Resource
        """
        self._logger.debug('Creating new resource {}'.format(resource))
        self._api.CreateResource(resource.family, resource.model, resource.name, resource.address)
        resource.exist = True
        if resource.driver:
            self._api.UpdateResourceDriver(resource.name, resource.driver)

        for attribute, value in resource.attributes.iteritems():
            if value:
                self._api.SetAttributeValue(resource.name, attribute, value)

    def autoload_resource(self, resource):
        """
        :type resource: cloudshell.layer_one.migration_tool.entities.resource.Resource
        """
        self._logger.debug('Autoloading resource {}'.format(resource))
        self._api.ExcludeResource(resource.name)

        # print "Autoloading resource {}...".format(self.name)
        self._api.AutoLoad(resource.name)
        # self.is_loaded = True
        self._api.IncludeResource(resource.name)

    def sync_from_device(self, resource):
        """
        :type resource: cloudshell.layer_one.migration_tool.entities.resource.Resource
        """
        self._logger.debug('SyncFromDevice resource {}'.format(resource))
        self._api.ExcludeResource(resource.name)
        self._api.SyncResourceFromDevice(resource.name)
        self._api.IncludeResource(resource.name)
