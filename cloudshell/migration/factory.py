import sys

import click
from backports.functools_lru_cache import lru_cache

from cloudshell.api.cloudshell_api import CloudShellAPISession
from cloudshell.logging.qs_logger import get_qs_logger
from cloudshell.migration.libs.quali_api import QualiAPISession


class CoreFactory(object):

    def __init__(self, configuration):
        """
        :param cloudshell.migration.config.Configuration configuration:
        """
        self._configuration = configuration

    @property
    @lru_cache()
    def logger(self):
        """
        :rtype: logging.Logger
        """
        # os.environ['LOG_PATH'] = configuration.log_path
        logger = get_qs_logger(str(self._configuration.PACKAGE_NAME), 'migration_tool', 'migration_tool')
        logger.setLevel(self._configuration.log_level)
        # click.echo('Log file: {}'.format(logger.handlers[0].baseFilename))
        return logger

    @property
    @lru_cache()
    def api(self):
        try:
            return CloudShellAPISession(self._configuration.host, self._configuration.username,
                                        self._configuration.password,
                                        self._configuration.domain, port=self._configuration.port)
        except IOError as e:
            click.echo('ERROR: Cannot initialize Cloudshell API connection, check API settings, details: {}'.format(e),
                       err=True)
            sys.exit(1)

    @property
    @lru_cache()
    def quali_api(self):
        return QualiAPISession(self._configuration.host, self._configuration.username, self._configuration.password,
                               self._configuration.domain)
