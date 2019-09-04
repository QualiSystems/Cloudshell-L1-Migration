import os


class ShowFlow(object):

    def __init__(self, logger, resource_operations):
        """
        :param logger:
        :param cloudshell.migration.core.operations.resource.ResourceOperations resource_operations:
        """
        self._logger = logger
        self._resource_operations = resource_operations

    def show_resources(self, family):
        resource_list = []
        for resource in self._resource_operations.installed_resources.values():
            if not family or resource.family == family:
                resource_list.append(resource.to_string())
        return os.linesep.join(resource_list)
