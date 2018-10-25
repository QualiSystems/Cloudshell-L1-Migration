class Resource(object):
    SEPARATOR = '/'
    USERNAME_ATTRIBUTE = 'User'
    PASSWORD_ATTRIBUTE = 'Password'

    def __init__(self, name, address=None, family=None, model=None, driver=None, exist=False):
        self.name = name
        self.address = address
        self.family = family
        self.model = model
        self.driver = driver
        self.ports = []
        self.associated_logical_routes = []

        self.attributes = {self.USERNAME_ATTRIBUTE: None, self.PASSWORD_ATTRIBUTE: None}
        self.exist = exist

    def to_string(self):
        ent_list = [self.name, self.family, self.model, self.driver]
        return self.SEPARATOR.join([ent for ent in ent_list if ent])

    def __str__(self):
        return self.to_string()

    def __eq__(self, other):
        return self.name == other.name

    def __repr__(self):
        return self.to_string()

    def __copy__(self):
        return Resource(self.name, self.address, self.family, self.model, self.driver, self.exist)

    @classmethod
    def from_string(cls, resource_string):
        """
        :type resource_string: str
        """
        return cls(*resource_string.split(cls.SEPARATOR))


class Port(object):
    def __init__(self, name, address=None, connected_to=None, connection_weight=None, associated_logical_route=None):
        self.name = name
        self.address = address
        self.connected_to = connected_to
        self.connection_weight = connection_weight
        # self.associated_logical_route = associated_logical_route

    def to_string(self):
        return 'Port: {}=>{}'.format(self.name, self.connected_to)
        # return 'Port: {}'.format(self.name)

    def __str__(self):
        return self.to_string()

    def __repr__(self):
        return self.to_string()

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return self.name == other.name

    def __lt__(self, other):
        return self.name < other.name


class LogicalRoute(object):
    def __init__(self, source, target, reservation_id, route_type, route_alias, active=True, shared=False):
        self.source = source
        self.target = target
        self.reservation_id = reservation_id
        self.route_type = route_type
        self.route_alias = route_alias
        self.active = active
        self.shared = shared

    def to_string(self):
        return '{0}<->{1}, {2}, {3}'.format(self.source, self.target, self.route_type,
                                            'Active' if self.active else 'Inactive')

    def __str__(self):
        return self.to_string()

    def __eq__(self, other):
        """
        :type other: LogicalRoute
        """
        return self.source == other.source and self.target == other.target

    def __hash__(self):
        return hash(self.source + self.target)
