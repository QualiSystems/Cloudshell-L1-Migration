from cloudshell.layer_one.migration_tool.entities.port import Port


class Connection(object):
    def __init__(self, port, connected_to, weight):
        """
        :type port:cloudshell.layer_one.migration_tool.entities.port.Port
        """
        self.port = port
        self.connected_to = connected_to
        self.weight = weight
        self.resource = None

    def __str__(self):
        return '{0}=>{1}'.format(self.port, self.connected_to)
