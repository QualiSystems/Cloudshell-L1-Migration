class ConfigUnit(object):
    NAME_INDEX = 0
    FAMILY_INDEX = 1
    MODEL_INDEX = 2
    DRIVER_INDEX = 3
    FORMAT = 'NAME/FAMILY/MODEL/DRIVER'
    EMPTY_CHARS = ['*', '.']
    SEPARATOR = '/'

    def __init__(self, config_str):
        """
        :type config_str: str
        """
        self.config_str = config_str

        self._config_list = None
        self.valid = False

    @property
    def resource_name(self):
        return self._get_config_field(self.NAME_INDEX)

    @property
    def resource_family(self):
        return self._get_config_field(self.FAMILY_INDEX)

    @property
    def resource_model(self):
        return self._get_config_field(self.MODEL_INDEX)

    @property
    def resource_driver(self):
        return self._get_config_field(self.DRIVER_INDEX)

    @property
    def config_list(self):
        if not self._config_list:
            self._config_list = self.config_str.split(self.SEPARATOR)
        return self._config_list

    def is_multi_resource(self):
        return self.config_list[0] in self.EMPTY_CHARS

    def _get_config_field(self, index):
        if len(self.config_list) > index and self.config_list[index] not in self.EMPTY_CHARS:
            return self.config_list[index]
