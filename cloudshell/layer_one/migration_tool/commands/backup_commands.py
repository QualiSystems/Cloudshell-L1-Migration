from cloudshell.layer_one.migration_tool.handlers.backup_config_handler import BackupConfigHandler


class BackupCommands(object):

    def __init__(self, api, logger, configuration, dry_run):
        """
        :type api: cloudshell.api.cloudshell_api.CloudShellAPISession
        :type logger: cloudshell.layer_one.migration_tool.helpers.logger.Logger
        """
        self._api = api
        self._logger = logger
        self._configuration = configuration
        self._dri_run = dry_run
        self._backup_config_handler = BackupConfigHandler(self._api, self._logger)

    def define_resources(self, resource_string):
        configs = self._backup_config_handler.parse_backup_configuration(resource_string)
        resources = []
        for config in configs:
            resources.extend(self._backup_config_handler.define_backup_resources(config))
        return resources

    def define_connections(self, resources):
        pass

    def define_logical_routes(self, resources):
        pass
