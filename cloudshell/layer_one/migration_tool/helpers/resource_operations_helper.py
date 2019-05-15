class ResourceHelper(object):
    def __init__(self, logger, config_helper, resource_operations):
        """
        :type logger: cloudshell.layer_one.migration_tool.helpers.logger.Logger
        :type config_helper: cloudshell.layer_one.migration_tool.helpers.config_helper.ConfigHelper
        :type resource_operations: cloudshell.layer_one.migration_tool.operations.resource_operations.ResourceOperations
        """
        self._logger = logger
        self._config_helper = config_helper
        self._resource_operations = resource_operations
        self._updated_connections = {}

    # def synchronize_resource_pair(self, resource_pair):
    #     # """
    #     # :type src_resource: cloudshell.layer_one.migration_tool.entities.Resource
    #     # :type dst_resource: cloudshell.layer_one.migration_tool.entities.Resource
    #     # """
    #     src_resource, dst_resource = resource_pair
    #     if not dst_resource.exist:
    #         if not dst_resource.name:
    #             dst_resource.name = self._config_helper.read_key(self._config_helper.NEW_RESOURCE_NAME_PREFIX_KEY,
    #                                                              self._config_helper.DEFAULT_CONFIGURATION.get(
    #                                                                  self._config_helper.NEW_RESOURCE_NAME_PREFIX_KEY
    #                                                              )) + src_resource.name
    #         dst_resource.address = src_resource.address
    #
    #         # self._synchronize_attributes(src_resource, dst_resource)
    #
    #     return src_resource, dst_resource

    # def synchronize_attributes(self, src_resource, dst_resource):
    #     """
    #     :param cloudshell.layer_one.migration_tool.entities.Resource src_resource:
    #     :param cloudshell.layer_one.migration_tool.entities.Resource dst_resource:
    #     """
    #     if 'l1 switch' in src_resource.model.lower():
    #         attributes_dict = self._config_helper.L1_ATTRIBUTES
    #     else:
    #         attributes_dict = self._config_helper.SHELLS_ATTRIBUTES
    #
    #     self._resource_operations.load_attributes(src_resource, attributes_dict.keys())
    #     dst_resource.attributes = src_resource.attributes
