from cloudshell.layer_one.migration_tool.entities.config_unit import ConfigUnit


class ArgumentParser(object):
    SEPARATOR = ','

    def __init__(self):
        pass

    def build_config_unit(self, single_argument):
        """
        :type single_argument: str
        """
        self._validate_argument(single_argument)
        return ConfigUnit(single_argument)

    def parse_argument_string(self, argument_str):
        """
        :type argument_str: str
        """
        return map(self.build_config_unit, argument_str.split(self.SEPARATOR))

    def _validate_argument(self, single_argument):
        pass
