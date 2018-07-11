class LogicalRoute(object):
    def __init__(self, source, target, reservation_id, route_type, route_alias, active=True, shared=False):
        self.source = source
        self.target = target
        self.reservation_id = reservation_id
        self.route_type = route_type
        self.route_alias = route_alias
        self.connections = []
        self.active = active
        self.shared = shared

    def __str__(self):
        return '{0}<->{1}, {2}, {3}'.format(self.source, self.target, self.route_type,
                                            'Active' if self.active else 'Inactive')
