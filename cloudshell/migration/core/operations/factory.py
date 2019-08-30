from backports.functools_lru_cache import lru_cache

from cloudshell.migration.core.operations.blueprint import TopologiesOperations, PackageOperations
from cloudshell.migration.core.operations.connection import ConnectionOperations
from cloudshell.migration.core.operations.connector import ConnectorOperations
from cloudshell.migration.core.operations.resource import ResourceOperations
from cloudshell.migration.core.operations.route import RouteOperations


class OperationsFactory(object):
    def __init__(self, core_factory, configuration, dry_run=False):
        """

        :param core_factory:
        :param cloudshell.migration.config.Configuration configuration:
        :param dry_run:
        """
        self._core_factory = core_factory
        self._configuration = configuration
        self._dry_run = dry_run

    @property
    @lru_cache()
    def resource_operations(self):
        return ResourceOperations(self._core_factory.api, self._core_factory.logger,
                                  self._configuration, self._dry_run)

    @property
    @lru_cache()
    def connection_operations(self):
        return ConnectionOperations(self._core_factory.api, self._core_factory.logger,
                                    self._configuration, self._dry_run)

    @property
    @lru_cache()
    def route_operations(self):
        return RouteOperations(self._core_factory.api, self._core_factory.logger,
                               self._configuration, self._dry_run)

    @property
    @lru_cache()
    def connector_operations(self):
        return ConnectorOperations(self._core_factory.api, self._core_factory.logger,
                                   self._configuration, self._dry_run)

    @property
    @lru_cache()
    def topologies_operations(self):
        return TopologiesOperations(self._core_factory.api, self._core_factory.logger,
                                    self._configuration, self._dry_run)

    @property
    @lru_cache()
    def package_operations(self):
        return PackageOperations(self._core_factory.quali_api, self._core_factory.logger, self._dry_run)
