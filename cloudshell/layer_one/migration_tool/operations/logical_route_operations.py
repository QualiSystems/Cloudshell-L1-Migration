from collections import defaultdict

from cloudshell.layer_one.migration_tool.entities import LogicalRoute


class LogicalRouteOperations(object):
    def __init__(self, api, logger, dry_run=False):
        """
        :type api: cloudshell.api.cloudshell_api.CloudShellAPISession
        :type logger: cloudshell.layer_one.migration_tool.helpers.logger.Logger
        """
        self._api = api
        self._logger = logger
        self._dry_run = dry_run
        # self._logical_routes = {}
        self._logical_routes_by_resource_name = defaultdict(set)
        self._logical_routes_by_segment = {}

    @property
    def logical_routes_by_resource_name(self):
        if not self._logical_routes_by_resource_name:
            active_routes = []
            for reservation in self._api.GetCurrentReservations().Reservations:
                if reservation.Id:
                    details = self._api.GetReservationDetails(reservation.Id).ReservationDescription
                    for route_info in details.ActiveRoutesInfo:
                        self._define_logical_route_by_resource_name(reservation.Id, route_info, True)
                        active_routes.append((route_info.Source, route_info.Target))
                    for route_info in details.RequestedRoutesInfo:
                        if (route_info.Source, route_info.Target) not in active_routes:
                            self._define_logical_route_by_resource_name(reservation.Id, route_info, False)
        return self._logical_routes_by_resource_name

    @property
    def logical_routes_by_segment(self):
        if not self._logical_routes_by_segment:
            active_routes = []
            for reservation in self._api.GetCurrentReservations().Reservations:
                if reservation.Id:
                    details = self._api.GetReservationDetails(reservation.Id).ReservationDescription
                    for route_info in details.ActiveRoutesInfo:
                        self._define_logical_route_by_segment(reservation.Id, route_info, True)
                        active_routes.append((route_info.Source, route_info.Target))
                    for route_info in details.RequestedRoutesInfo:
                        if (route_info.Source, route_info.Target) not in active_routes:
                            self._define_logical_route_by_segment(reservation.Id, route_info, False)
        return self._logical_routes_by_segment

    def _define_logical_route_by_resource_name(self, reservation_id, route_info, active=True):
        source = route_info.Source
        target = route_info.Target
        route_type = route_info.RouteType
        route_alias = route_info.Alias
        shared = route_info.Shared
        logical_route = LogicalRoute(source, target, reservation_id, route_type, route_alias, active, shared)
        for segment in route_info.Segments:
            self._logical_routes_by_resource_name[segment.Source.split('/')[0]].add(logical_route)
            self._logical_routes_by_resource_name[segment.Target.split('/')[0]].add(logical_route)

    def _define_logical_route_by_segment(self, reservation_id, route_info, active=True, handled_logical_routes=[]):
        source = route_info.Source
        target = route_info.Target
        route_type = route_info.RouteType
        route_alias = route_info.Alias
        shared = route_info.Shared
        if source and target:
            logical_route = LogicalRoute(source, target, reservation_id, route_type, route_alias, active, shared)
            if route_info.Segments and logical_route not in handled_logical_routes:
                handled_logical_routes.append(logical_route)
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
        :type resource: cloudshell.layer_one.migration_tool.entities.Resource
        """
        logical_routes_table = []
        for port in resource.ports:
            logical_route = self.logical_routes_by_segment.get(port.name)
            if logical_route and logical_route not in logical_routes_table:
                logical_routes_table.append(logical_route)
            # port.associated_logical_route = logical_route
            # if logical_route and logical_route not in resource.associated_logical_routes:
            #     resource.associated_logical_routes.append(logical_route)
        return logical_routes_table

    def define_associated_logical_routes(self, resource):
        """
        :type resource: cloudshell.layer_one.migration_tool.entities.Resource
        """
        logical_routes_table = self.get_logical_routes_table(resource)
        resource.associated_logical_routes = [route for route, endpoint in logical_routes_table if endpoint]
        return resource

    def remove_route(self, logical_route):
        """
        :type logical_route: cloudshell.layer_one.migration_tool.entities.logical_route.LogicalRoute
        """
        self._logger.debug('Removing logical route {}'.format(logical_route))
        if not self._dry_run:
            self._api.RemoveRoutesFromReservation(logical_route.reservation_id,
                                                  [logical_route.source, logical_route.target],
                                                  logical_route.route_type)

    def create_route(self, logical_route):
        """
        :type logical_route: cloudshell.layer_one.migration_tool.entities.logical_route.LogicalRoute
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
