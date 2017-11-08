import os.path
import json
import sys
from cloudshell.api.common_cloudshell_api import CloudShellAPIError
from cloudshell.api.cloudshell_api import CloudShellAPISession


class Memory:
    """
    This class is intended to keep relevant data in json files, and interact with the file.
    """
    def __init__(self, name):
        self.path = "data/{}.json".format(name)
        try:
            self.data = self.restore()
        except ValueError:
            self.data = {}

    def set(self, key, value):
        self.data[key] = value
        self.save()
        return

    def get(self, key):
        return self.data.get(key)

    def restore(self):
        return json.loads(open(self.path, 'r').read())

    def save(self):
        f = open(self.path, 'w')
        f.write(json.dumps(self.data))
        f.close()
        return

    def clear(self):
        f = open(self.path, 'w')
        f.close()


CREDENTIALS_PATH = 'config/forms/credentials.json'
RESOURCE_NAMES_PATH = 'config/forms/resource_names.json'
NEW_RESOURCE_PATH = 'config/forms/new_resource.json'


class Form:
    """
    This is a base class for keeping user configurations inside json files, and interacting with them.
    """
    def __init__(self, path):
        self.path = path

    def read(self):
        with open(self.path, 'r') as f:
            try:
                content = json.loads(f.read())
                return content
            except ValueError:
                return []

    def get(self, field):
        pass

    def set(self, field, value):
        pass

    def add(self, value):
        pass


class DictForm(Form):
    """
    Class 
    """
    def __init__(self, path):
        Form.__init__(self, path)

    def get(self, field):
        return self.read()[field]['value']

    def set(self, field, value):
        content = self.read()
        content[field]['value'] = value
        with open(self.path, 'w') as f:
            f.write(json.dumps(content))


class ListForm(Form):

    def __init__(self, path):
        Form.__init__(self, path)

    def get(self, field):
        pass

    def set(self, field, value):
        pass

    def add(self, value):
        content = self.read()
        content.append(value)
        with open(self.path, 'w') as f:
            f.write(json.dumps(content))

    def clear(self):
        f = open(self.path, 'w')
        f.close()


class PathParser:
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


class Resource:
    def __init__(self, name, api, folder=''):
        self.api = api
        self.name = name
        self.folder = folder
        try:
            self.resource = self.api.GetResourceDetails(self.name)
        except CloudShellAPIError:
            self.resource = None
        self.full_path = os.path.join(self.folder, self.name)

    def physical_connections(self):
        resource_physical_connections = []
        for child_resource in self.resource.ChildResources:
            for grandchild_resource in child_resource.ChildResources:
                if len(grandchild_resource.Connections) > 0:
                    resource_physical_connections.append({'source': BladePortParser(grandchild_resource.Name),
                                                          'target': grandchild_resource.Connections[0].FullPath})
        return resource_physical_connections

    def get_credentials(self):
        return {
            'User': self.api.GetAttributeValue(self.full_path, 'User').Value,
            'Password': self.api.DecryptPassword(api.GetAttributeValue(self.full_path, 'Password').Value).Value,
        }

    def create_and_autoload(self):
        pass


class OldResource(Resource):
    def __init__(self, name, folder=''):
        Resource.__init__(self, name, folder)
        self.is_converted = False
        self.new_resource = NewResource("new_{}".format(self.name), self.folder, old_resource=self)


class NewResource(Resource):
    def __init__(self, name,  api, folder='', **kwargs):
        self.api = api
        self.old_resource = kwargs['old_resource'] if 'old_resource' in kwargs else None
        Resource.__init__(self, name, folder)
        self.is_created = False
        self.is_loaded = False
        self.is_converted = False
        self.ip_address = self.old_resource.resource.FullAddress

    def create(self):
        print "Creating resource {}...".format(self.name)
        # self.api.CreateResource('L1 Switch', 'Generic MRV Chassis', self.name, self.ip_address)
        new_resource_data = json.loads(open("forms/new_resource.json", 'r').read())
        self.api.CreateResource(new_resource_data['family'], new_resource_data['model'], self.name, self.ip_address)
        self.is_created = True
        self.api.UpdateResourceDriver(self.name, new_resource_data['driver'])
        self.resource = self.api.GetResourceDetails(self.name)

    def autoload(self):
        self.api.ExcludeResource(self.name)
        credentials = self.old_resource.get_credentials()
        for attr in credentials:
            self.api.SetAttributeValue(self.name, attr, credentials[attr])
        print "Autoloading resource {}...".format(self.name)
        self.api.AutoLoad(self.name)
        self.is_loaded = True
        self.api.IncludeResource(self.name)
        print "Autoload for resource {} done.".format(self.name)
        self.resource = self.api.GetResourceDetails(self.name)


class OldToNewMRVConverter:
    def __init__(self, new_resource_names_prefix, relevant_resource_names_list, api):
        self.api = api
        self.new_resource_names_prefix = new_resource_names_prefix
        self.relevant_resource_names = relevant_resource_names_list
        self.logical_routes_memory = Memory('logical_routes')
        self.resources_memory = Memory('resources')

    def topologies(self):
        return [x for x in self.api.GetFolderContent('').ContentArray if x.Type == 'Topology']

    def blueprints(self):
        blueprints = []
        for topology in self.topologies():
            if topology.Name not in [name for name in self.api.GetActiveTopologyNames().Topologies]:
                blueprints.append(topology)
        return blueprints

    def reservations(self):
        return self.api.GetCurrentReservations().Reservations

    def get_topology_by_name(self, name):
        try:
            return [x for x in self.topologies() if x.Name == name][0]
        except IndexError:
            return None

    def get_reservation_by_topology_name(self, name):
        for reservation in self.api.GetCurrentReservations().Reservations:
            if reservation.Name == name:
                return self.api.GetReservationDetails(reservation.Id)
        return None

    def memory_keep_logical_routes(self):
        for reservation in self.reservations():
            handler = ReservationHandler(converter, api, reservation_id=reservation.Id)
            logical_routes = [{'route': x, 'status': 'connected'} for x in handler.logical_routes()]
            self.logical_routes_memory.set(reservation.Id, {'logical_routes': logical_routes})

    def memory_keep_physical_connections(self):
        for resource_name in self.relevant_resource_names:
            old_resource = OldResource(resource_name)
            new_resource_name = old_resource.new_resource.name

            # Validating resource is in memory
            if new_resource_name not in self.resources_memory.data:
                self.resources_memory.set(new_resource_name, {'is_loaded': False, 'is_created': False, 'is_converted': False})

            # Creating new resource if neeeded
            if self.resources_memory.get(new_resource_name)['is_created'] is False:
                old_resource.new_resource.create()
                mem_curr_data = self.resources_memory.get(new_resource_name)
                mem_curr_data['is_created'] = True
                resources_memory.set(new_resource_name, mem_curr_data)

            # Autoloading new resource if neeeded
            if self.resources_memory.get(new_resource_name)['is_loaded'] is False:
                old_resource.new_resource.autoload()
                mem_curr_data = resources_memory.get(new_resource_name)
                mem_curr_data['is_loaded'] = True
                self.resources_memory.set(new_resource_name, mem_curr_data)

            # Moving physical connections from old resource to new resource
            for old_physical_connection in old_resource.physical_connections():
                new_source_port = "/".join([old_resource.new_resource.name, old_physical_connection['source'].new_format()])
                self.api.UpdatePhysicalConnection(new_source_port, old_physical_connection['target'])

    def reconnect_relevant_routes(self):
        for reservation_id in self.logical_routes_memory.data:
            handler = ReservationHandler(self, self.api, reservation_id=reservation_id)
            logical_routes = self.logical_routes_memory.get(reservation_id)['logical_routes']
            for logical_route in logical_routes:
                try:
                    handler.reconnect_route(logical_route['route']['source'], logical_route['route']['target'])
                except CloudShellAPIError as e:
                    try:
                        resource_name = re.findall("'\w+'", e.message)[0].replace("'", "")
                        api.ExcludeResource(resource_name)
                        api.SyncResourceFromDevice(resource_name)
                        api.IncludeResource(resource_name)
                        handler.reconnect_route(logical_route['route']['source'], logical_route['route']['target'])
                    except IndexError:
                        print e.message

    def convert(self):
        self.memory_keep_logical_routes()
        self.memory_keep_physical_connections()
        self.reconnect_relevant_routes()

        # Clearing memory files
        self.resources_memory.clear()
        self.logical_routes_memory.clear()


class ReservationHandler:
    def __init__(self, converter, api, **kwargs):
        self.api = api
        self.converter = converter
        self.topology_name = kwargs['topology_name'] if 'topology_name' in kwargs else None
        self.reservation_id = kwargs['reservation_id'] if 'reservation_id' in kwargs else None
        if self.reservation_id is not None:
            self.reservation_name = self.api.GetReservationDetails(self.reservation_id).ReservationDescription.Name
            self.reservation = self.api.GetReservationDetails(self.reservation_id).ReservationDescription
        else:
            self.reservation_name = self.topology_name if self.topology_name is not None else kwargs['reservation'].Name
            self.reservation = self.converter.get_reservation_by_topology_name(self.reservation_name)

    def logical_routes(self):
        return [{'source': x.Source, 'target': x.Target} for x in self.reservation.ActiveRoutesInfo]

    def relevant_logical_routes(self):
        return [{'source': x.Source, 'target': x.Target} for x in self.reservation.ActiveRoutesInfo if
                self.is_route_consisting_of_relevant_resource(x)]

    @staticmethod
    def get_top_hierarchy_resource_name_from_name(name):
        return "/".join(name.split("/")[:-2])

    def is_route_consisting_of_relevant_resource(self, route):
        for segment in route.Segments:
            source_resource = self.converter.api.GetResourceDetails(
                self.get_top_hierarchy_resource_name_from_name(segment.Source))
            target_resource = self.converter.api.GetResourceDetails(
                self.get_top_hierarchy_resource_name_from_name(segment.Target))
            if self.is_relevant(source_resource) or self.is_relevant(target_resource):
                return True
        return False

    def is_relevant(self, resource_object):
        return resource_object.Name in self.converter.relevant_resource_names

    def reconnect_route(self, source, target):
        self.api.RemoveRoutesFromReservation(self.reservation_id, [source, target], 'bi')
        print "Disconnected route between {} and {} in reservation id {}".format(source, target, self.reservation_id)
        self.api.CreateRouteInReservation(self.reservation_id, source, target, False, 'bi', 2, 'Alias', False)
        print "Connected route between {} and {} in reservation id {}".format(source, target, self.reservation_id)

    def find_relevant_resources(self):
        resources = []
        for resource in self.converter.reservation.ReservationDescription.Resources:
            if resource.Name in self.converter.relevant_resource_names:
                resources.append(resource)
        return resources

    def get_all_routes(self):
        return self.converter.topology.Routes

    @staticmethod
    def get_active_routes(reservation_description):
        return reservation_description.ActiveRoutesInfo


if __name__ == '__main__':
    credentials = DictForm(CREDENTIALS_PATH)
    new_resource_template = DictForm(NEW_RESOURCE_PATH)
    resource_names = ListForm(RESOURCE_NAMES_PATH)

    if "--config" in sys.argv:
        if sys.argv[sys.argv.index("--config") + 1] == "/f":
            filepath = sys.argv[sys.argv.index("--config") + 2]
        else:
            field = sys.argv[sys.argv.index("--config") + 1]
            value = sys.argv[sys.argv.index("--config") + 2]
            credentials.set(field, value)

    if "--resources" in sys.argv:
        if sys.argv[sys.argv.index("--resources") + 1] == "/a":
            resource_name = sys.argv[sys.argv.index("--resources") + 2]
            resource_names.add(resource_name)
        elif sys.argv[sys.argv.index("--resources") + 1] == "--clear":
            resource_names.clear()

    if "--new-resource" in sys.argv:
        if sys.argv[sys.argv.index("--new-resource") + 1] == "/f":
            resources_filepath = sys.argv[sys.argv.index("--resources") + 2]
            resources_list = open(resources_filepath, 'r').read().split('\n')
            resource_names.clear()
            [resource_names.add(name) for name in resources_list]
        else:
            field = sys.argv[sys.argv.index("--new-resource") + 1]
            value = sys.argv[sys.argv.index("--new-resource") + 2]
            new_resource_template.set(field, value)

    if len(sys.argv) == 2 and 'convert' in sys.argv:
        api = CloudShellAPISession(credentials.get('host'), credentials.get('username'), credentials.get('password'), credentials.get('domain'))
        converter = OldToNewMRVConverter("new_", resource_names.read(), api)