import os

import yaml

from cloudshell.layer_one.migration_tool.entities.resource import Resource
from cloudshell.layer_one.migration_tool.helpers.config_helper import ConfigHelper
from cloudshell.layer_one.migration_tool.helpers.logical_route_helper import LogicalRouteHelper
from cloudshell.layer_one.migration_tool.helpers.resource_operation_helper import ResourceOperationHelper


class BackupCommands(object):
    SEPARATOR = ','

    def __init__(self, api, logger, configuration, backup_file):
        self._api = api
        self._logger = logger
        self._configuration = configuration
        self._backup_file = backup_file or self._backup_file_path()

        self._resource_operation_helper = ResourceOperationHelper(api, logger, dry_run=False)
        self._logical_route_helper = LogicalRouteHelper(api, logger, dry_run=False)

    def _backup_file_path(self):
        backup_path = self._configuration.get(ConfigHelper.BACKUP_LOCATION_KEY)
        if not backup_path:
            raise Exception(self.__class__.__name__, 'Backup location was not specified')
        filename = 'backup.yaml'
        return os.path.join(backup_path, filename)

    def _write_to_file(self, data):
        if not os.path.exists(self._backup_file):
            os.makedirs(os.path.dirname(self._backup_file))
        with open(self._backup_file, 'w') as backup_file:
            backup_file.write(data)

    def define_resources(self, resources_string):
        """
        :param resources_string:
        :type resources_string: str
        :rtype:list
        """
        return map(Resource.from_string, resources_string.split(self.SEPARATOR))

    def backup_resources(self, resources):
        for resource in resources:
            resource.connections = self._resource_operation_helper.get_physical_connections(resource).values()
            resource.logical_routes = list(self._logical_route_helper.logical_routes_by_resource_name.get(resource.name))
        data = yaml.dump(resources, default_flow_style=False, allow_unicode=True, encoding=None)
        self._write_to_file(data)

