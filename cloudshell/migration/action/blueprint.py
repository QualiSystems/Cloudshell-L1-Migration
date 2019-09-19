from collections import defaultdict

from cloudshell.migration.action.core import Action, ActionsContainer


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

    @staticmethod
    def initialize_for_pair(resource_pair, override, associations_table, operations_factory, logger):
        src_resource = resource_pair.src_resource
        topologies_operations = operations_factory.topologies_operations
        routes, connectors = topologies_operations.logical_routes_connectors_by_resource_name.get(
            src_resource.name, ([], []))
        blueprint_table = defaultdict(lambda: ([], []))
        for route in routes:
            blueprint_table[route.blueprint][0].append(route)

        for connector in connectors:
            blueprint_table[connector.blueprint][1].append(connector)

        actions = []
        for blueprint_name, data in blueprint_table.items():
            actions.append(
                UpdateBlueprintAction(blueprint_name, data[0], data[1], operations_factory.package_operations,
                                      associations_table,
                                      logger))
        return ActionsContainer(actions)
