class Resource(object):
    USERNAME_ATTRIBUTE = 'User'
    PASSWORD_ATTRIBUTE = 'Password'

    def __init__(self, name, address=None, family=None, model=None, driver=None, exist=False):
        self.name = name
        self.address = address
        self.family = family
        self.model = model
        self.driver = driver

        self.attributes = {self.USERNAME_ATTRIBUTE: None, self.PASSWORD_ATTRIBUTE: None}
        self.exist = exist

    def description(self):
        ent_list = [self.name, self.family, self.model, self.driver]
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
