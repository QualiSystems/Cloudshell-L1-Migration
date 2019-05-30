import os
from datetime import datetime

import yaml

from cloudshell.migration.exceptions import MigrationToolException
from cloudshell.migration.operations.argument_operations import ArgumentOperations


class BackupHandler(object):
    SEPARATOR = ','
    RESOURCES_KEY = 'RESOURCES'
    LOGICAL_ROUTES_KEY = 'LOGICAL_ROUTES'

    def __init__(self, api, logger, config_operations, backup_file, resource_operations, logical_route_operations):
        """
        :type api: cloudshell.api.cloudshell_api.CloudShellAPISession
        :type logger: cloudshell.migration.helpers.log_helper.Logger
        :type config_operations: cloudshell.migration.operations.config_operations.ConfigOperations
        :type backup_file: str
        :type resource_operations: cloudshell.migration.operations.resource_operations.ResourceOperations
        :type logical_route_operations: cloudshell.migration.operations.route_connector_operations.RouteConnectorOperations
        """
        self._api = api
        self._logger = logger
        self._config_operations = config_operations
        self._backup_file = backup_file or self._backup_file_path()

        self._resource_operations = resource_operations
        self._logical_route_operations = logical_route_operations

    def _backup_file_path(self):
        backup_path = self._config_operations.read_key_or_default(self._config_operations.KEY.BACKUP_LOCATION)
        if not backup_path:
            raise MigrationToolException('Backup location was not specified')
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
        if resources_arguments:
            return ArgumentOperations(self._logger, self._resource_operations).initialize_existing_resources(
                resources_arguments)
        else:
            return self._resource_operations.resources

    def backup_resources(self, resources, connections=True, routes=True, connectors=True):
        self._logger.info('Doing backup ...')
        if not connections and not routes and not connectors:
            connections = routes = connectors = True

        # logical_routes = set()
        for resource in resources:
            self._resource_operations.update_details(resource)
            if not resource.attributes:
                self._resource_operations.load_resource_attributes(resource)
            if connections and not resource.ports:
                self._resource_operations.load_resource_ports(resource)
                # self._resource_operations.load_resource_attributes(resource)
            if routes and not resource.associated_logical_routes:
                self._logical_route_operations.load_logical_routes(resource)
                # logical_routes.update(resource.associated_logical_routes)
            if connectors and not resource.associated_connectors:
                self._logical_route_operations.load_connectors(resource)

        # backup_dict = {self.RESOURCES_KEY: resources,
        #                self.LOGICAL_ROUTES_KEY: list(logical_routes)}

        # self._resource_operations.define_port_connections(*resources)

        data = yaml.dump(resources, default_flow_style=False, allow_unicode=True, encoding=None)
        self._write_to_file(data)
        self._logger.info('Backup file {}'.format(self._backup_file))
        return self._backup_file
