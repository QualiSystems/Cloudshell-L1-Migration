from cloudshell.migration.action.core import Action, ActionsContainer


class UpdateConnectionAction(Action):
    ACTION_DESCR = "Update Connection"
    priority = Action._EXECUTION_STAGE.ONE

    def __init__(self, src_port, dst_port, connection_operations, updated_connections, logger):
        """
        :param cloudshell.migration.core.entities.Port src_port:
        :param cloudshell.migration.core.entities.Port dst_port:
        :param cloudshell.migration.core.operations.connection.ConnectionOperations connection_operations:
        :param dict updated_connections:
        :param logging.Logger logger:
        """
        super(UpdateConnectionAction, self).__init__(logger)
        self.src_port = src_port
        self.dst_port = dst_port
        self.connection_operations = connection_operations
        self.updated_connections = updated_connections

    def description(self):
        return '{} ({}=>{})'.format(self.ACTION_DESCR, self.dst_port.name, self.src_port.connected_to)

    def execute(self):
        self.dst_port.connected_to = self.updated_connections.get(self.src_port.connected_to,
                                                                  self.src_port.connected_to)
        self.connection_operations.update_connection(self.dst_port)
        self.updated_connections[self.src_port.name] = self.dst_port.name

    @property
    def _comparable_unit(self):
        return ''.join([self.src_port.name, self.src_port.connected_to or ''])

    def __hash__(self):
        return hash(self._comparable_unit)

    def __eq__(self, other):
        """
        :type other: UpdateConnectionAction
        """
        return Action.__eq__(self, other) and self._comparable_unit == other._comparable_unit

    @staticmethod
    def initialize_for_pair(resource_pair, override, associations_table, operations_factory, logger):
        connection_actions = []

        for src_port, dst_port in resource_pair.associator.iter_pairs():
            if override or not dst_port.connected_to:
                connection_actions.append(
                    UpdateConnectionAction(src_port, dst_port, operations_factory.connection_operations,
                                           resource_pair.updated_connections, logger))
        return ActionsContainer(connection_actions)
