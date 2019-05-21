from collections import defaultdict

from backports.functools_lru_cache import lru_cache

from cloudshell.layer_one.migration_tool.entities import Port, Resource


class ResourceOperations(object):
    L1_FAMILY = 'L1 Switch'

    def __init__(self, api, logger, config_helper, dry_run=False):
        """
        :type api: cloudshell.api.cloudshell_api.CloudShellAPISession
        :type logger: cloudshell.layer_one.migration_tool.helpers.logger.Logger
        :type config_helper: cloudshell.layer_one.migration_tool.helpers.config_helper.ConfigHelper
        """
        self._api = api
        self._logger = logger
        self._config_helper = config_helper
        self._dry_run = dry_run

    @lru_cache()
    def _get_resource_details(self, resource):
        return self._api.GetResourceDetails(resource.name)

    @property
    @lru_cache()
    def installed_resources(self):
        """
        :rtype: dict
        """
        installed_resources = {}
        for resource_info in self._api.GetResourceList().Resources:
            resource = Resource(resource_info.Name, resource_info.Address, resource_info.ResourceFamilyName,
                                resource_info.ResourceModelName, exist=True)
            installed_resources[resource.name] = resource
        return installed_resources

    @property
    @lru_cache()
    def sorted_by_family_model_resources(self):
        resources_by_family_model = defaultdict(list)
        for resource in self.installed_resources.values():
            resources_by_family_model[(resource.family, resource.model)].append(resource)
        return resources_by_family_model

    @property
    def l1_resources(self):
        return [resource for name, resource in self.installed_resources.iteritems() if
                resource.family == self.L1_FAMILY]

    def _is_l1_resource(self, resource):
        resource_details = self._get_resource_details(resource)
        if resource_details.ResourceFamilyName in self._config_helper.L1_FAMILIES:
            return True
        else:
            return False

    def load_resource_attributes(self, resource):
        """
        :type resource: cloudshell.layer_one.migration_tool.entities.Resource
        """

        resource_details = self._get_resource_details(resource)
        resource_attr_dict = {attr.Name: attr for attr in resource_details.ResourceAttributes}
        if self._is_l1_resource(resource):
            attribute_list = self._config_helper.L1_ATTRIBUTES
        else:
            attribute_list = self._config_helper.SHELLS_ATTRIBUTES

        for attr_name in attribute_list:
            attribute = resource_attr_dict.get(attr_name, None) or resource_attr_dict.get(
                '.'.join([resource_details.ResourceFamilyName, attr_name]), None) or resource_attr_dict.get(
                '.'.join([resource_details.ResourceModelName, attr_name]), None)
            resource.attributes[attr_name] = attribute
        return resource

    def update_details(self, resource):
        """
        :type resource: cloudshell.layer_one.migration_tool.entities.Resource
        """
        resource_details = self._get_resource_details(resource)
        resource.address = resource_details.RootAddress
        resource.driver = resource_details.DriverName
        # self.define_resource_ports(resource)
        # self.define_resource_attributes(resource)
        return resource

    def load_resource_ports(self, resource):
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
        if not resource_info.ChildResources and resource_info.ResourceFamilyName in self._config_helper.PORT_FAMILIES:
            return True
        else:
            return False

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
        # resource.exist = True
        if resource.driver:
            self._api.UpdateResourceDriver(resource.name, resource.driver)
        return resource

    def set_resource_attributes(self, resource):
        for name, attribute in resource.attributes.items():
            value = attribute.Value
            if value:
                if attribute.Type == 'Password':
                    try:
                        value = self._api.DecryptPassword(value).Value
                    except:
                        pass
                self._api.SetAttributeValue(resource.name, attribute.Name, value)

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
