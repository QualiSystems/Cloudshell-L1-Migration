class ConfigUnit(object):
    NAME_INDEX = 0
    FAMILY_INDEX = 1
    MODEL_INDEX = 2
    DRIVER_INDEX = 3
    FORMAT = 'NAME/FAMILY/MODEL/DRIVER'
    EMPTY_CHARS = ['*', '.']
    SEPARATOR = '/'

    def __init__(self, config_str):
        """
        :type config_str: str
        """
        self.config_str = config_str

        self._config_list = None
        self.valid = False

    @property
    def resource_name(self):
        return self._get_config_field(self.NAME_INDEX)

    @property
    def resource_family(self):
        return self._get_config_field(self.FAMILY_INDEX)

    @property
    def resource_model(self):
        return self._get_config_field(self.MODEL_INDEX)

    @property
    def resource_driver(self):
        return self._get_config_field(self.DRIVER_INDEX)

    @property
    def config_list(self):
        if not self._config_list:
            self._config_list = self.config_str.split(self.SEPARATOR)
        return self._config_list

    def is_multi_resource(self):
        return self.config_list[0] in self.EMPTY_CHARS

    def _get_config_field(self, index):
        if len(self.config_list) > index and self.config_list[index] not in self.EMPTY_CHARS:
            return self.config_list[index]


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

    @classmethod
    def from_string(cls, resource_string):
        """
        :type resource_string: str
        """
        return cls(*resource_string.split(cls.SEPARATOR))


class LogicalRoute(object):
    def __init__(self, source, target, reservation_id, route_type, route_alias, active=True, shared=False):
        self.source = source
        self.target = target
        self.reservation_id = reservation_id
        self.route_type = route_type
        self.route_alias = route_alias
        # self.connections = []
        self.active = active
        self.shared = shared

    def __str__(self):
        return '{0}<->{1}, {2}, {3}'.format(self.source, self.target, self.route_type,
                                            'Active' if self.active else 'Inactive')

    def __eq__(self, other):
        """
        :type other: LogicalRoute
        """
        return self.source == other.source and self.target == other.target
