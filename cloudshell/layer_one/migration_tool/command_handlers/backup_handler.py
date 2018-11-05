import os
from datetime import datetime

import yaml
from cloudshell.layer_one.migration_tool.helpers.config_helper import ConfigHelper
from cloudshell.layer_one.migration_tool.operations.logical_route_operations import LogicalRouteOperations
from cloudshell.layer_one.migration_tool.operations.argument_parser import ArgumentParser
from cloudshell.layer_one.migration_tool.operations.resource_operations import ResourceOperations


class BackupHandler(object):
    SEPARATOR = ','
    RESOURCES_KEY = 'RESOURCES'
    LOGICAL_ROUTES_KEY = 'LOGICAL_ROUTES'

    def __init__(self, api, logger, configuration, backup_file):
        self._api = api
        self._logger = logger
        self._configuration = configuration
        self._backup_file = backup_file or self._backup_file_path()

        self._resource_operations = ResourceOperations(api, logger)
        self._logical_route_operations = LogicalRouteOperations(api, logger, dry_run=False)

    def _backup_file_path(self):
        backup_path = self._configuration.get(ConfigHelper.BACKUP_LOCATION_KEY)
        if not backup_path:
            raise Exception(self.__class__.__name__, 'Backup location was not specified')
        filename = datetime.now().strftime('%Y-%m-%d_%H-%M-%S') + '.yaml'
        return os.path.join(backup_path, filename)

    def _write_to_file(self, data):
        dir_path = os.path.dirname(self._backup_file)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        with open(self._backup_file, 'w') as backup_file:
            backup_file.write(data)

    def initialize_resources(self, resources_arguments):
        """
        :type resources_arguments: str
        :rtype:list
        """
        return ArgumentParser(self._logger, self._resource_operations).initialize_existing_resources(
            resources_arguments)

    def backup_resources(self, resources, connections=True, routes=True):
        self._logger.info('Backup resources')
        if not connections and not routes:
            connections = routes = True

        logical_routes = set()
        for resource in resources:
            if connections:
                self._resource_operations.update_details(resource)
            if routes:
                # resource.associated_logical_routes = list(
                #     self._logical_route_operations.logical_routes_by_resource_name.get(resource.name, []))

                self._logical_route_operations.define_logical_routes(resource)
                logical_routes.update(resource.associated_logical_routes)

        # backup_dict = {self.RESOURCES_KEY: resources,
        #                self.LOGICAL_ROUTES_KEY: list(logical_routes)}

        # self._resource_operations.define_port_connections(*resources)

        data = yaml.dump(resources, default_flow_style=False, allow_unicode=True, encoding=None)
        self._write_to_file(data)
