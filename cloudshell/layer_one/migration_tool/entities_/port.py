class Port(object):
    def __init__(self, name, address, connected_to=None, connection_weight=None):
        self.name = name
        self.address = address
        self.connected_to = connected_to
        self.connection_weight = connection_weight

    def to_string(self):
        return 'Port:{}=>{}'.format(self.name, self.connected_to)

    def __str__(self):
        return self.to_string()

    def __repr__(self):
        return self.to_string()
