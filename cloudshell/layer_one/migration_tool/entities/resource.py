class Resource(object):
    DESCRIPTION_HEADER = 'Name/Address/Family/Model/Driver'

    def __init__(self, name, address=None, family=None, model=None, driver=None):
        self.name = name
        self.address = address
        self.family = family
        self.model = model
        self.driver = driver

    def description(self):
        ent_list = [self.name, self.address, self.family, self.model, self.driver]
        return '/'.join([ent for ent in ent_list if ent])

    def __str__(self):
        return self.description()

    def __eq__(self, other):
        return self.name == other.name

    @classmethod
    def from_string(cls, resource_string):
        """
        :type resource_string: str
        """
        return cls(*resource_string.split('/'))
