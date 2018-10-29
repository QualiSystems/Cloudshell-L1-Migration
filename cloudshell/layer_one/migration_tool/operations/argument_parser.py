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
        self._validate_argument(single_argument)
        return ConfigUnit(single_argument)

    def parse_argument_string(self, argument_str):
        """
        :type argument_str: str
        """
        return map(self.build_config_unit, argument_str.split(self.RESOURCE_SEPARATOR))

    def _validate_argument(self, single_argument):
        pass

    def initialize_resources_for_argument_string(self, resources_argument, existing_only=False):
        """
        :type resources_argument: str
        :type existing_only: bool
        :rtype:list
        """
        resources = []
        for config_unit in self.parse_argument_string(resources_argument):
            resources.extend(self.initialize_resources_for_config_unit(config_unit))
        if existing_only:
            return [resource for resource in resources if resource.exist]
        return resources

    def initialize_resources_for_config_unit(self, config_unit):
        """
        :type config_unit: cloudshell.layer_one.migration_tool.operational_entities.config_unit.ConfigUnit
        """
        if config_unit.is_multi_resource():
            resources = self._resource_operations.sorted_by_family_model_resources.get((config_unit.resource_family,
                                                                                        config_unit.resource_model),
                                                                                       [config_unit.empty_resource()])
        else:
            resources = [self._resource_operations.installed_resources.get(config_unit.resource_name,
                                                                           config_unit.empty_resource())]
        return resources
