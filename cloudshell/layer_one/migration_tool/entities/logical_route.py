class LogicalRoute(object):
    def __init__(self, source, target, reservation_id):
        self.source = source
        self.target = target
        self.reservation_id = reservation_id
        self.connections = []

    def __str__(self):
        return '{0}->{1}'.format(self.source, self.target)
