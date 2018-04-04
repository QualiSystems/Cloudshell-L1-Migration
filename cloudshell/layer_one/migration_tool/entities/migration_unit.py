class MigrationUnit(object):
    def __init__(self, old_resource, new_resource):
        self.old_resource = old_resource
        self.new_resource = new_resource

    def __str__(self):
        return '{0}->{1}'.format(str(self.old_resource), str(self.new_resource))

    def __repr__(self):
        return self.__str__()
