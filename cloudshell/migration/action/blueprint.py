from cloudshell.migration.action.core import Action


class UpdateBlueprintAction(Action):
    ACTION_DESCR = "Update Blueprint"
    priority = Action._EXECUTION_STAGE.THREE

    def __init__(self, blueprint_name, routes, connectors, package_operations, associations_table, logger):
        """
        :param blueprint_name:
        :param routes:
        :param connectors:
        :param package_operations:
        :param associations_table:
        :param logger:
        """
        super(UpdateBlueprintAction, self).__init__(logger)
        self.blueprint_name = blueprint_name
        self.routes = set(routes)
        self.connectors = set(connectors)
        self._package_operations = package_operations
        self._associations_table = associations_table

    def execute(self):
        self._package_operations.load_package(self.blueprint_name)
        for ent in list(self.routes) + list(self.connectors):
            self._logger.debug('Remove : {}'.format(ent))
            self._package_operations.remove_route_connector(ent.source, ent.target)
        self._update_endpoints(self.routes)
        self._update_endpoints(self.connectors)
        for route in self.routes:
            self._logger.debug('Add {}'.format(route))
            self._package_operations.add_route(route)

        for connector in self.connectors:
            self._logger.debug('Add {}'.format(connector))
            self._package_operations.add_connector(connector)

        self._package_operations.update_topology()

    def _update_endpoints(self, ent_list):
        for ent in ent_list:
            ent.source = self._associations_table.get(ent.source, ent.source)
            ent.target = self._associations_table.get(ent.target, ent.target)

    def description(self):
        return "{} {}".format(self.ACTION_DESCR, self.blueprint_name)

    def __hash__(self):
        return hash(self.blueprint_name)

    def __eq__(self, other):
        return Action.__eq__(self, other) and self.blueprint_name == other.blueprint_name

    def merge(self, action):
        """
        :param BlueprintAction action:
        """
        self.routes = set(self.routes) | set(action.routes)
        self.connectors = set(self.connectors) | set(action.connectors)
