class LogicalRoute(object):
    def __init__(self, source, target, reservation_id, route_type, route_alias, active=True):
        self.source = source
        self.target = target
        self.reservation_id = reservation_id
        self.route_type = route_type
        self.route_alias = route_alias
        self.connections = []
        self.active = active

    def __str__(self):
        return '{0}<->{1}'.format(self.source, self.target)
