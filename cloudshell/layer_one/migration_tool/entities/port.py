class Port(object):
    def __init__(self, name, address):
        self.address = address
        self.name = name

    def __str__(self):
        return self.name
