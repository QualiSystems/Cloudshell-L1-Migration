from collections import defaultdict

from backports.functools_lru_cache import lru_cache

from cloudshell.api.cloudshell_api import SetConnectorRequest
from cloudshell.migration.entities import LogicalRoute, Connector


class RouteConnectorOperations(object):
    def __init__(self, api, logger, dry_run=False):
        """
        :type api: cloudshell.api.cloudshell_api.CloudShellAPISession
        :type logger: cloudshell.migration.helpers.log_helper.Logger
        """
        self._api = api
        self._logger = logger
        self._dry_run = dry_run
        # self._logical_routes = {}
        self._logical_routes_by_resource_name = defaultdict(set)
        self._logical_routes_by_segment = {}
        self._handled_logical_routes = []

    @property
    @lru_cache()
    def _reservations(self):
        return self._api.GetCurrentReservations().Reservations

    @lru_cache()
    def _reservation_details(self, reservation_id):
        return self._api.GetReservationDetails(reservation_id).ReservationDescription

    # @property
    # def logical_routes_by_resource_name(self):
    #     if not self._logical_routes_by_resource_name:
    #         active_routes = []
    #         for reservation in self._api.GetCurrentReservations().Reservations:
    #             if reservation.Id:
    #                 details = self._api.GetReservationDetails(reservation.Id).ReservationDescription
    #                 for route_info in details.ActiveRoutesInfo:
    #                     self._define_logical_route_by_resource_name(reservation.Id, route_info, True)
    #                     active_routes.append((route_info.Source, route_info.Target))
    #                 for route_info in details.RequestedRoutesInfo:
    #                     if (route_info.Source, route_info.Target) not in active_routes:
    #                         self._define_logical_route_by_resource_name(reservation.Id, route_info, False)
    #     return self._logical_routes_by_resource_name

    @property
    @lru_cache()
    def logical_routes_by_segment(self):
        if not self._logical_routes_by_segment:
            active_routes = []
            for reservation in self._reservations:
                if reservation.Id:
                    details = self._reservation_details(reservation.Id)
                    for route_info in details.ActiveRoutesInfo:
                        self._define_logical_route_by_segment(reservation.Id, route_info, True)
                        active_routes.append((route_info.Source, route_info.Target))
                    for route_info in details.RequestedRoutesInfo:
                        if (route_info.Source, route_info.Target) not in active_routes:
                            self._define_logical_route_by_segment(reservation.Id, route_info, False)
        return self._logical_routes_by_segment

    # def _define_logical_route_by_resource_name(self, reservation_id, route_info, active=True):
    #     source = route_info.Source
    #     target = route_info.Target
    #     route_type = route_info.RouteType
    #     route_alias = route_info.Alias
    #     shared = route_info.Shared
    #     logical_route = LogicalRoute(source, target, reservation_id, route_type, route_alias, active, shared)
    #     for segment in route_info.Segments:
    #         self._logical_routes_by_resource_name[segment.Source.split('/')[0]].add(logical_route)
    #         self._logical_routes_by_resource_name[segment.Target.split('/')[0]].add(logical_route)

    def _define_logical_route_by_segment(self, reservation_id, route_info, active=True):
        source = route_info.Source
        target = route_info.Target
        route_type = route_info.RouteType
        route_alias = route_info.Alias
        shared = route_info.Shared
        if source and target:
            logical_route = LogicalRoute(source, target, reservation_id, route_type, route_alias, active, shared)
            if route_info.Segments and logical_route not in self._handled_logical_routes:
                self._handled_logical_routes.append(logical_route)
                self._add_segment(logical_route, route_info.Segments[0], True)
                self._add_segment(logical_route, route_info.Segments[-1], True)

                for segment in route_info.Segments[1:-1]:
                    self._add_segment(logical_route, segment, False)

    def _add_segment(self, logical_route, segment, endpoint):
        if not self._logical_routes_by_segment.get(segment.Source):
            self._logical_routes_by_segment[segment.Source] = (logical_route, endpoint)
        if not self._logical_routes_by_segment.get(segment.Target):
            self._logical_routes_by_segment[segment.Target] = (logical_route, endpoint)

        # for segment in route_info.Segments:
        #     self._logical_routes_by_resource_name[segment.Source.split('/')[0]].add(logical_route)
        #     self._logical_routes_by_resource_name[segment.Target.split('/')[0]].add(logical_route)

    def get_logical_routes_table(self, resource):
        """
        :type resource: cloudshell.migration.entities.Resource
        """
        logical_routes_table = []
        for port in resource.ports:
            if port.connected_to:
                logical_route = self.logical_routes_by_segment.get(port.name)
                if logical_route and logical_route not in logical_routes_table:
                    logical_routes_table.append(logical_route)
            # port.associated_logical_route = logical_route
            # if logical_route and logical_route not in resource.associated_logical_routes:
            #     resource.associated_logical_routes.append(logical_route)
        return logical_routes_table

    def define_endpoint_logical_routes(self, resource):
        """
        :type resource: cloudshell.migration.entities.Resource
        """
        logical_routes_table = self.get_logical_routes_table(resource)
        resource.associated_logical_routes = [route for route, endpoint in logical_routes_table if endpoint]
        return resource

    def load_logical_routes(self, resource):
        """
        :type resource: cloudshell.migration.entities.Resource
        """
        logical_routes_table = self.get_logical_routes_table(resource)
        resource.associated_logical_routes = list(set([route for route, endpoint in logical_routes_table]))
        return resource

    def remove_route(self, logical_route):
        """
        :type logical_route: cloudshell.migration.entities.logical_route.LogicalRoute
        """
        self._logger.debug('Removing logical route {}'.format(logical_route))
        if not self._dry_run:
            self._api.RemoveRoutesFromReservation(logical_route.reservation_id,
                                                  [logical_route.source, logical_route.target],
                                                  logical_route.route_type)

    def create_route(self, logical_route):
        """
        :type logical_route: cloudshell.migration.entities.logical_route.LogicalRoute
        """
        self._logger.debug('Creating logical route {}'.format(logical_route))
        if not self._dry_run:
            if logical_route.active:
                self._api.CreateRouteInReservation(logical_route.reservation_id, logical_route.source,
                                                   logical_route.target,
                                                   False, logical_route.route_type, 2, logical_route.route_alias,
                                                   logical_route.shared)
            else:
                self._api.AddRoutesToReservation(logical_route.reservation_id, [logical_route.source],
                                                 [logical_route.target],
                                                 logical_route.route_type, 2, logical_route.route_alias,
                                                 logical_route.shared)

    def load_connectors(self, resource):
        """
        :type resource: cloudshell.migration.entities.Resource
        """
        resource.associated_connectors = self._connectors_by_resource_name.get(resource.name, [])
        return resource

    @property
    @lru_cache()
    def _connectors_by_resource_name(self):
        connector_by_resource_name = defaultdict(list)
        for reservation in self._reservations:
            if reservation.Id:
                details = self._reservation_details(reservation.Id)
                for connector in details.Connectors:
                    if connector.Source and connector.Target:
                        connector_ent = Connector(connector.Source, connector.Target, reservation.Id,
                                                  connector.Direction, connector.Type, connector.Alias)
                        connector_by_resource_name[connector.Source.split('/')[0]].append(connector_ent)
                        connector_by_resource_name[connector.Target.split('/')[0]].append(connector_ent)
        return connector_by_resource_name

    def update_connector(self, connector):
        """
        :param cloudshell.migration.entities.Connector connector:
        :return:
        """
        self._logger.debug('Updating connector {}'.format(connector))
        self._api.SetConnectorsInReservation(connector.reservation_id, [
            SetConnectorRequest(connector.source, connector.target, connector.direction, connector.alias)])

    def remove_connector(self, connector):
        """
        :param cloudshell.migration.entities.Connector connector:
        :return:
        """
        self._logger.debug('Removing connector {}'.format(connector))
        self._api.RemoveConnectorsFromReservation(connector.reservation_id, [connector.source, connector.target])
