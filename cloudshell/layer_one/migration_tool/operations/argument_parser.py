from cloudshell.layer_one.migration_tool.exceptions import MigrationToolException
from cloudshell.layer_one.migration_tool.operational_entities.config_unit import ConfigUnit


class ArgumentParser(object):
    RESOURCE_SEPARATOR = ','

    def __init__(self, logger, resource_operations):
        self._logger = logger
        self._resource_operations = resource_operations

    def build_config_unit(self, single_argument):
        """
        :type single_argument: str
        """
        single_argument = single_argument.strip()
        self._validate_argument(single_argument)
        return ConfigUnit(single_argument)

    def parse_argument_string(self, argument_str):
        """
        :type argument_str: str
        """
        argument_list = argument_str.split(self.RESOURCE_SEPARATOR) if argument_str else []
        return map(self.build_config_unit, argument_list)

    def _validate_argument(self, single_argument):
        pass

    def initialize_existing_resources(self, resources_argument):
        """
        :type resources_argument: str
        :rtype:list
        """
        resources = []
        for config_unit in self.parse_argument_string(resources_argument):
            if config_unit.is_multi_resource():
                resources_list = self._resource_operations.sorted_by_family_model_resources.get(
                    (config_unit.resource_family, config_unit.resource_model))

            else:
                resources_list = [self._resource_operations.installed_resources.get(config_unit.resource_name)]
            if resources_list:
                resources.extend(resources_list)
            else:
                raise MigrationToolException('Cannot find resources for {}'.format(config_unit.config_str))
        return resources

    def initialize_resources_with_stubs(self, resources_argument):
        """
        :type resources_argument: str
        :rtype:list
        """
        resources = []
        for config_unit in self.parse_argument_string(resources_argument):
            if config_unit.is_multi_resource():
                resources.append(config_unit.stub_resource())
            else:
                resources.append(self._resource_operations.installed_resources.get(
                    config_unit.resource_name) or config_unit.stub_resource())
        return resources
