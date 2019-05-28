import traceback


class ExceptionLogger(object):
    def __init__(self, logger):
        self._logger = logger

    def __enter__(self):
        return self._logger

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val:
            self._logger.critical(traceback.format_exc())
            # sys.exit(1)
            # else:
            return False
