import sys

import click
from backports.functools_lru_cache import lru_cache

from cloudshell.api.cloudshell_api import CloudShellAPISession
from cloudshell.logging.qs_logger import get_qs_logger
from cloudshell.migration.libs.quali_api import QualiAPISession
from cloudshell.migration.operations.blueprint_operations import TopologiesOperations, PackageOperations
from cloudshell.migration.operations.connection_operations import ConnectionOperations
from cloudshell.migration.operations.connector_operations import ConnectorOperations
from cloudshell.migration.operations.resource_operations import ResourceOperations
from cloudshell.migration.operations.route_operations import RouteOperations


class Factory(object):

    def __init__(self, configuration, dry_run=False):
        """
        :param cloudshell.migration.config.Configuration configuration:
        """
        self.configuration = configuration
        self.dry_run = dry_run

    @property
    @lru_cache()
    def logger(self):
        # os.environ['LOG_PATH'] = configuration.log_path
        logger = get_qs_logger(str(self.configuration.PACKAGE_NAME), 'migration_tool', 'migration_tool')
        logger.setLevel(self.configuration.log_level)
        # click.echo('Log file: {}'.format(logger.handlers[0].baseFilename))
        return logger

    @property
    @lru_cache()
    def api(self):
        try:
            return CloudShellAPISession(self.configuration.host, self.configuration.username,
                                        self.configuration.password,
                                        self.configuration.domain, port=self.configuration.port)
        except IOError as e:
            click.echo('ERROR: Cannot initialize Cloudshell API connection, check API settings, details: {}'.format(e),
                       err=True)
            sys.exit(1)

    @property
    @lru_cache()
    def quali_api(self):
        return QualiAPISession(self.configuration.host, self.configuration.username, self.configuration.password,
                               self.configuration.domain)

    @property
    @lru_cache()
    def resource_operations(self):
        return ResourceOperations(self.api, self.logger, self.configuration, self.dry_run)

    @property
    @lru_cache()
    def connection_operations(self):
        return ConnectionOperations(self.api, self.logger, self.configuration, self.dry_run)

    @property
    @lru_cache()
    def route_operations(self):
        return RouteOperations(self.api, self.logger, self.configuration, self.dry_run)

    @property
    @lru_cache()
    def connector_operations(self):
        return ConnectorOperations(self.api, self.logger, self.configuration, self.dry_run)

    @property
    @lru_cache()
    def topologies_operations(self):
        return TopologiesOperations(self.api, self.logger, self.configuration, self.dry_run)

    @property
    @lru_cache()
    def package_operations(self):
        return PackageOperations(self.quali_api, self.logger, self.dry_run)
