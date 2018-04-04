class ResourceValidator(object):
    def __init__(self, api):
        """
        :type api: cloudshell.api.cloudshell_api.CloudShellAPISession
        """
        self._api = api

    def new_resource_is_valid(self, resource):
        """
        :type resource: cloudshell.layer_one.migration_tool.entities.resource.Resource
        """
        return True

    def old_resource_is_valid(self, resource):
        """
        :type resource: cloudshell.layer_one.migration_tool.entities.resource.Resource
        """
        return True

    def validate_new_resource(self, new_resource, old_resource):
        pass

    def validate_old_resource(self, resource):
        pass
