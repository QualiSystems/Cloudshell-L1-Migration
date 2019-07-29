import os
import tempfile
import zipfile
from collections import defaultdict
from random import randint
from xml.etree.ElementTree import Element

from backports.functools_lru_cache import lru_cache

from cloudshell.migration.entities import LogicalRoute, Connector
from cloudshell.migration.helpers.xml_helper import XMLHelper
from cloudshell.migration.operations.operations import Operations


class TopologiesOperations(Operations):

    @property
    @lru_cache()
    def active_topologies(self):
        topologies = []
        for reservation in self._reservations:
            topologies.extend(reservation.Topologies)
        return topologies

    @property
    @lru_cache()
    def _topologies(self):
        def _get_topologies(folder):
            topo_list = []
            for content in self._api.GetFolderContent(folder).ContentArray:
                topo_path = '/'.join([folder, content.Name] if folder else [content.Name])
                if content.Type == 'Folder':
                    topo_list.extend(_get_topologies(topo_path))
                elif content.Type == 'Topology':
                    topo_list.append(topo_path)
            return topo_list

        return _get_topologies('')

    @property
    @lru_cache()
    def _inactive_topologies(self):
        return list(set(self._topologies) - set(self.active_topologies))

    @property
    @lru_cache()
    def routes_connectors(self):
        routes = []
        connectors = []
        for topo in self._inactive_topologies:
            self._logger.debug('Topology path: {}'.format(topo))
            try:
                topo_details = self._api.GetTopologyDetails(topo)
            except Exception as e:
                self._logger.error(e.message)
                continue
            if topo_details.Type != 'Template':
                for route in topo_details.Routes:
                    if route.Source and route.Target:
                        routes.append(
                            LogicalRoute(route.Source, route.Target, None, route.RouteType, route.Alias, False,
                                         route.Shared, blueprint=topo_details.Name))
                for connector in topo_details.Connectors:
                    if connector.Source and connector.Target:
                        connectors.append(
                            Connector(connector.Source, connector.Target, None, connector.Direction, connector.Type,
                                      connector.Alias, False, blueprint=topo_details.Name))
        return routes, connectors

    @property
    @lru_cache()
    def logical_routes_connectors_by_resource_name(self):
        routes_connectors_table = defaultdict(lambda: ([], []))
        for route in self.routes_connectors[0]:
            routes_connectors_table[route.source.split('/')[0]][0].append(route)
            routes_connectors_table[route.target.split('/')[0]][0].append(route)
        for connector in self.routes_connectors[1]:
            routes_connectors_table[connector.source.split('/')[0]][1].append(connector)
            routes_connectors_table[connector.target.split('/')[0]][1].append(connector)
        return routes_connectors_table


class PackageOperations(object):
    ROUTE_XML_TEMPLATE = '<Route Source="" Target="" MaxHops="2" Direction="" Shared="" />'
    CONNECTOR_XML_TEMPLATE = '<Connector Source="" Target="" Direction="" />'
    RESOURCE_XML_TEMPLATE = '<Resource Name="" Shared="true">'

    # SUB_RESOURCE_XML_TEMPLATE='<Resource Name="Chassis 1" Shared="true"/>'
    def __init__(self, quali_api, logger, dry_run):
        """
        :type quali_api: cloudshell.migration.libs.quali_api.QualiAPISession
        :type logger: cloudshell.migration.helpers.log_helper.Logger
        """
        self._quali_api = quali_api
        self._logger = logger
        self._dry_run = dry_run
        self._tmp_dir = tempfile.mkdtemp()
        self._package_name = None
        self._package_file = None
        self._new_package_file = None
        self._root_node = None

    @property
    def _topologies_file(self):
        return 'Topologies/' + self._package_name + '.xml'

    def load_package(self, blueprint_name):
        """
        :param str blueprint_name:
        :return:
        """
        self._package_name = blueprint_name
        self._package_file = os.path.join(self._tmp_dir, self._package_name + '.zip')
        self._new_package_file = os.path.join(self._tmp_dir, self._package_name + '_new' + '.zip')
        self._quali_api.ExportPackage([self._package_name], self._package_file)
        with zipfile.ZipFile(self._package_file, 'r') as zip_file:
            with zip_file.open(self._topologies_file) as myfile:
                self._root_node = XMLHelper.build_node_from_string(myfile.read())

    def update_topology(self):
        # with zipfile.ZipFile(self._package_file, 'a') as zip_file:
        #     with zip_file.open('Topologies/' + bp_name + '.xml') as myfile:
        # zip_file.writestr(self._topologies_file, XMLHelper.to_string(self._root_node))
        # return XMLHelper.to_string(self._root_node)
        #     tempdir = tempfile.mkdtemp()
        #     try:
        #         tempname = os.path.join(tempdir, 'new.zip')
        with zipfile.ZipFile(self._package_file, 'r') as zipread:
            with zipfile.ZipFile(self._new_package_file, 'w') as zipwrite:
                for item in zipread.infolist():
                    if item.filename != self._topologies_file:
                        data = zipread.read(item.filename)
                        zipwrite.writestr(item, data)
                    else:
                        zipwrite.writestr(item, XMLHelper.to_string(self._root_node))

        self._quali_api.ImportPackage(self._new_package_file)

    @property
    def routes(self):
        routes = {}
        for route in self._root_node.findall('Routes/Route') or []:
            source = route.get('Source')
            target = route.get('Target')
            r_type = route.get('Direction')
            shared = route.get('Shared')
            route_ent = LogicalRoute(source, target, None, r_type, None, False, shared)
            routes[source] = route_ent
            routes[target] = route_ent
        return routes

    @property
    def connectors(self):
        connectors = {}
        for connector in self._root_node.findall('Routes/Connector') or []:
            source = connector.get('Source')
            target = connector.get('Target')
            direction = connector.get('Direction')
            route_ent = Connector(source, target, None, direction, None, False)
            connectors[source] = route_ent
            connectors[target] = route_ent
        return connectors

    @property
    def resources(self):
        resources = []

        def _build_names(node):
            _names = []
            _name = node.get('Name')
            _child_nodes = node.findall('SubResources/Resource') or []
            if _child_nodes:
                for _child_node in _child_nodes:
                    _names.extend(map(lambda n: _name + '/' + n, _build_names(_child_node)))
            else:
                _names.append(_name)

            return _names

        for resource_node in self._root_node.find('Resources') or []:
            names = _build_names(resource_node)
            resources.extend(names)
        return resources

    def _get_or_append_sub_resource(self, name, root_node, shared='true'):
        for node in root_node.findall('SubResources/Resource') or []:
            if node.get('Name') == name:
                return node
        sub_resources = root_node.find('SubResources')
        if sub_resources is None:
            sub_resources = Element('SubResources')
            root_node.append(sub_resources)
        resource = Element('Resource')
        resource.set('Name', name)
        resource.set('Shared', str(shared).lower())
        sub_resources.append(resource)
        return resource

    def _get_or_append_resource(self, name, shared='true'):
        resources_node = self._root_node.find('Resources')
        if resources_node is None:
            raise Exception('Cannot find <Resources> XML node')

        for node in resources_node:
            if node.get('Name') == name:
                return node
        if resources_node is None:
            resources_node = Element('Resources')
            self._root_node.append(resources_node)
        resource = Element('Resource')
        resource.set('Name', name)
        resource.set('Shared', str(shared).lower())
        resource.set('PositionX', str(randint(100, 1000)))
        resource.set('PositionY', str(randint(100, 1000)))
        resources_node.append(resource)
        return resource

    def _add_resource(self, resource_str):
        name_list = resource_str.split('/')
        node = self._get_or_append_resource(name_list[0])
        for sub_name in name_list[1:-1]:
            node = self._get_or_append_sub_resource(sub_name, node)
        return self._get_or_append_sub_resource(name_list[-1], node, 'false')

    def add_route(self, route):
        """
        :param cloudshell.migration.entities.LogicalRoute route:
        """
        node = XMLHelper.build_node_from_string(self.ROUTE_XML_TEMPLATE)
        node.set("Source", route.source)
        node.set("Target", route.target)
        node.set("Direction", route.route_type.capitalize())
        node.set("Shared", str(route.shared).lower())
        routes_node = self._root_node.find('Routes')
        """:type routes_node: xml.etree.ElementTree.Element"""
        routes_node.insert(0, node)
        self._add_resource(route.source)
        self._add_resource(route.target)

    def add_connector(self, connector):
        """
        :param cloudshell.migration.entities.Connector connector:
        """
        node = XMLHelper.build_node_from_string(self.CONNECTOR_XML_TEMPLATE)
        node.set("Source", connector.source)
        node.set("Target", connector.target)
        node.set("Direction", connector.direction.capitalize())
        routes_node = self._root_node.find('Routes')
        routes_node.append(node)
        self._add_resource(connector.source)
        self._add_resource(connector.target)

    def remove_route_connector(self, source, target):
        """
        :param cloudshell.migration.entities.LogicalRoute route:
        """
        routes_node = self._root_node.find('Routes')
        if routes_node is not None:
            for route in routes_node:
                if source == route.get('Source') and target == route.get('Target'):
                    routes_node.remove(route)

    # def remove_connector(self, connector):
    #     pass

    def __del__(self):
        os.remove(self._package_file)
        os.remove(self._new_package_file)
        os.rmdir(self._tmp_dir)
