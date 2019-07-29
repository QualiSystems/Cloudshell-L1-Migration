import os

from cloudshell.migration.entities import Resource
from cloudshell.migration.operational_entities.config_unit import ConfigUnit
from cloudshell.migration.operations.resource_operations import ResourceOperations


class ResourcesHandler(object):

    def __init__(self, logger, resource_operations):
        """
        :param logger:
        :param cloudshell.migration.operations.resource_operations.ResourceOperations resource_operations:
        """
        self._logger = logger
        self._resource_operations = resource_operations

    def show_resources(self, family):
        resource_list = []
        for resource in self._resource_operations.installed_resources:
            if not family or resource.family == family:
                resource_list.append(resource.to_string())
        return os.linesep.join(resource_list)
