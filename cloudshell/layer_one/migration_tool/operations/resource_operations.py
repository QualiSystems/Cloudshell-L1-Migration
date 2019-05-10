from collections import defaultdict

from cloudshell.layer_one.migration_tool.entities import Port, Resource


class ResourceOperations(object):
    L1_FAMILY = 'L1 Switch'
    PORT_MARKERS = ['port']

    def __init__(self, api, logger, dry_run=False):
        """
        :type api: cloudshell.api.cloudshell_api.CloudShellAPISession
        :type logger: cloudshell.layer_one.migration_tool.helpers.logger.Logger
        """
        self._api = api
        self._logger = logger
        self._dry_run = dry_run
        self._resource_details_container = {}
        self._installed_resources = {}
        self._resources_by_family_model = {}

    def _get_resource_details(self, resource):
        if resource.name not in self._resource_details_container:
            self._resource_details_container[resource.name] = self._api.GetResourceDetails(resource.name)
        return self._resource_details_container.get(resource.name)

    @property
    def installed_resources(self):
        """
        :rtype: dict
        """
        if not self._installed_resources:
            for resource_info in self._api.GetResourceList().Resources:
                resource = Resource(resource_info.Name, resource_info.Address, resource_info.ResourceFamilyName,
                                    resource_info.ResourceModelName, exist=True)
                self._installed_resources[resource.name] = resource
        return self._installed_resources

    @property
    def sorted_by_family_model_resources(self):
        if not self._resources_by_family_model:
            self._resources_by_family_model = defaultdict(list)
            for resource in self.installed_resources.values():
                self._resources_by_family_model[(resource.family, resource.model)].append(resource)
        return self._resources_by_family_model

    @property
    def l1_resources(self):
        return [resource for name, resource in self.installed_resources.iteritems() if resource.family == self.L1_FAMILY]

    def define_resource_attributes(self, resource):
        """
        :type resource: cloudshell.layer_one.migration_tool.entities.Resource
        """
        for attribute in resource.attributes:
            value = self._api.GetAttributeValue(resource.name, attribute).Value
            resource.attributes[attribute] = value

    def update_details(self, resource):
        """
        :type resource: cloudshell.layer_one.migration_tool.entities.Resource
        """
        resource_details = self._get_resource_details(resource)
        resource.address = resource_details.RootAddress
        resource.driver = resource_details.DriverName
        self.define_resource_ports(resource)
        # self.define_resource_attributes(resource)
        return resource

    def define_resource_ports(self, resource):
        """
        :type resource: cloudshell.layer_one.migration_tool.entities.Resource
        """
        self._logger.debug('Getting ports for resource {}'.format(resource.name))
        resource_details = self._get_resource_details(resource)
        resource.ports = self._get_ports(resource_details)
        return resource

    def _get_ports(self, resource_info):
        """
        :param resource_info: cloudshell.api.cloudshell_api.ResourceInfo
        """
        ports = []
        if self._is_it_a_port(resource_info):
            ports.append(self._build_port(resource_info))
        else:
            for child_resource_info in resource_info.ChildResources:
                ports.extend(self._get_ports(child_resource_info))
        return ports

    def _is_it_a_port(self, resource_info):
        """
        :type resource_info: cloudshell.api.cloudshell_api.ResourceInfo
        """
        if not resource_info.ChildResources:
            for marker in self.PORT_MARKERS:
                if marker in resource_info.ResourceFamilyName.lower() or marker in resource_info.ResourceModelName.lower():
                    return True

    def _build_port(self, resource_info):
        """
        :param resource_info: cloudshell.api.cloudshell_api.ResourceInfo
        """
        if resource_info.Connections:
            connected_to = resource_info.Connections[0].FullPath
            # connected_to = Port(resource_info.Connections[0].FullPath)
            connection_weight = resource_info.Connections[0].Weight
        else:
            connected_to = None
            connection_weight = None
        return Port(resource_info.Name, resource_info.FullAddress, connected_to, connection_weight)

    def create_resource(self, resource):
        """
        :type resource: cloudshell.layer_one.migration_tool.entities.Resource
        """
        self._logger.debug('Creating new resource {}'.format(resource))
        self._api.CreateResource(resource.family, resource.model, resource.name, resource.address)
        resource.exist = True
        if resource.driver:
            self._api.UpdateResourceDriver(resource.name, resource.driver)

        for attribute, value in resource.attributes.iteritems():
            if value:
                if attribute == resource.PASSWORD_ATTRIBUTE:
                    value = self._api.DecryptPassword(value).Value
                self._api.SetAttributeValue(resource.name, attribute, value)
        return resource

    def autoload_resource(self, resource):
        """
        :type resource: cloudshell.layer_one.migration_tool.entities.Resource
        """
        self._logger.debug('Autoloading resource {}'.format(resource))
        self._api.ExcludeResource(resource.name)

        # print "Autoloading resource {}...".format(self.name)
        self._api.AutoLoad(resource.name)
        # self.is_loaded = True
        self._api.IncludeResource(resource.name)
        return resource

    def sync_from_device(self, resource):
        """
        :type resource: cloudshell.layer_one.migration_tool.entities.Resource
        """
        self._logger.debug('SyncFromDevice resource {}'.format(resource))
        self._api.ExcludeResource(resource.name)
        self._api.SyncResourceFromDevice(resource.name)
        self._api.IncludeResource(resource.name)
        return resource

    def update_connection(self, port):
        """
        :type port: cloudshell.layer_one.migration_tool.entities.Port
        """
        self._logger.info('---- Updating Connection {}=>{}'.format(port.name, port.connected_to))
        if not self._dry_run:
            self._api.UpdatePhysicalConnection(port.name, port.connected_to or '')
            if port.connected_to and port.connection_weight:
                self._api.UpdateConnectionWeight(port.name, port.connected_to, port.connection_weight)

    # @staticmethod
    # def define_port_connections(*resources):
    #     ports = []
    #     map(lambda x: ports.extend(x.ports), resources)
    #     for port in ports:
    #         if port.connected_to and port.connected_to in ports:
    #             port.connected_to = ports[ports.index(port.connected_to)]
    #     print ports
