import re

class ResourceOperationHelper(object):
    def __init__(self, api):
        self._api = api

    def get_logical_routes(self, resource):
        """
        :type resource: cloudshell.layer_one.migration_tool.entities.resource.Resource
        """
        routes = []
        for reservation in self._api.GetCurrentReservations().Reservations:
            if reservation.Id:
                details = self._api.GetReservationDetails(reservation.Id).ReservationDescription
                routes.extend([{'source': x.Source, 'target': x.Target} for x in details.ActiveRoutesInfo])
        return routes


    def get_physical_connections(self, resource):
        """
        :type resource: cloudshell.layer_one.migration_tool.entities.resource.Resource
        """
        resource_details = self._api.GetResourceDetails(resource.name)
        resource_physical_connections = []
        for child_resource in resource_details.ChildResources:
            for grandchild_resource in child_resource.ChildResources:
                if len(grandchild_resource.Connections) > 0:
                    resource_physical_connections.append({'source': BladePortParser(grandchild_resource.Name),
                                                          'target': grandchild_resource.Connections[0].FullPath})
        return resource_physical_connections





class PathParser:
    """
    Due to differences in the naming conventions of sub-resources between the old MRV shells to the new one (Port01 vs /Port 1,
    I created this class in order to handle the migration between the two conventions easily.
    """
    def __init__(self, path):
        self.path = path
        self.type = ''
        self.num = -1
        self.parse()

    def parse(self):
        try:
            self.type = re.findall("[A-z]+", self.path)[0]
        except IndexError:
            self.type = None
        try:
            self.num = str(int(re.findall("\d+", self.path)[0]))
        except IndexError:
            self.num = None

    def num_to_str(self):
        return str(self.num) if int(self.num) > 9 else "0{}".format(str(self.num))

    def old_format(self):
        return "{}{}".format(self.type.lower().title(), self.num_to_str())

    def new_format(self):
        return "{}{}".format(self.type.lower().title(), self.num)

    def __eq__(self, other):
        return self.type == other.type and self.num == other.num

class BladePortParser:
    """
    This class is uses PathParsers in order to migrate two physical connections (Blade01/Port01 to Blade 1/Port 1 etc.)
    """
    def __init__(self, path):
        self.path = path
        self.bladeport = self.path.split("/")[::-1][:2][::-1]
        self.blade = PathParser(self.bladeport[0])
        self.port = PathParser(self.bladeport[1])

    def old_format(self):
        return "/".join([self.blade.old_format(), self.port.old_format()])

    def new_format(self):
        return "/".join([self.blade.new_format(), self.port.new_format()])

    def __repr__(self):
        return "/".join(self.bladeport)