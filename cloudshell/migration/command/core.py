class Command(object):
    def __init__(self, configuration, logger):
        """
        :param cloudshell.migration.configuration.config.Configuration configuration:
        :param logging.Logger logger:
        """
        self._configuration = configuration
        self._logger = logger
