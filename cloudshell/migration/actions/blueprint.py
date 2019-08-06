from cloudshell.migration.actions.core import Action


class UpdateBlueprintAction(Action):
    def __init__(self, blueprint_name, routes, connectors, quali_api, associations_table, logger):
        """
        :param blueprint_name:
        :param routes:
        :param connectors:
        :param quali_api:
        :param associations_table:
        :param logger:
        """
        super(UpdateBlueprintAction, self).__init__(logger)
        self.blueprint_name = blueprint_name
        self.routes = set(routes)
        self.connectors = set(connectors)
        self.quali_api = quali_api
        self._associations_table = associations_table

    def execute(self):
        self.logger.debug("Executing action for blueprint {}".format(self.blueprint_name))
        package_operations = PackageOperations(self.quali_api, self.logger)
        try:
            package_operations.load_package(self.blueprint_name)
            for ent in list(self.routes) + list(self.connectors):
                self.logger.debug('Remove : {}'.format(ent))
                package_operations.remove_route_connector(ent.source, ent.target)
            self._update_endpoints(self.routes)
            self._update_endpoints(self.connectors)
            for route in self.routes:
                self.logger.debug('Add {}'.format(route))
                package_operations.add_route(route)

            for connector in self.connectors:
                self.logger.debug('Add {}'.format(connector))
                package_operations.add_connector(connector)

            package_operations.update_topology()
            return self.to_string() + " ... Done"
        except Exception as e:
            self.logger.error('Update blueprint {} failed, reason {}'.format(self.blueprint_name, e.message))
            return self.to_string() + "... Failed"

    def _update_endpoints(self, ent_list):
        for ent in ent_list:
            ent.source = self._associations_table.get(ent.source, ent.source)
            ent.target = self._associations_table.get(ent.target, ent.target)

    def to_string(self):
        return "Update Blueprint: {}".format(self.blueprint_name)

    def __hash__(self):
        return hash(self.blueprint_name)

    def __eq__(self, other):
        return self.blueprint_name == other.blueprint_name

    def merge(self, action):
        """
        :param BlueprintAction action:
        """
        self.routes = set(self.routes) | set(action.routes)
        self.connectors = set(self.connectors) | set(action.connectors)
