from collections import defaultdict

from cloudshell.layer_one.migration_tool.entities.logical_route import LogicalRoute


class LogicalRouteHelper(object):
    def __init__(self, api, logger, dry_run):
        """
        :type api: cloudshell.api.cloudshell_api.CloudShellAPISession
        :type logger: cloudshell.layer_one.migration_tool.helpers.logger.Logger
        """
        self._api = api
        self._logger = logger
        self._dry_run = dry_run
        self._logical_routes = {}
        self._logical_routes_by_resource_name = defaultdict(set)

    @property
    def logical_routes_by_segments(self):
        if not self._logical_routes:
            for reservation in self._api.GetCurrentReservations().Reservations:
                if reservation.Id:
                    details = self._api.GetReservationDetails(reservation.Id).ReservationDescription
                    for route_info in details.ActiveRoutesInfo:
                        source = route_info.Source
                        target = route_info.Target
                        logical_route = LogicalRoute(source, target, reservation.Id)
                        for segment in route_info.Segments:
                            self._logical_routes[segment.Source] = logical_route
                            self._logical_routes[segment.Target] = logical_route
        return self._logical_routes

    @property
    def logical_routes_by_resource_name(self):
        if not self._logical_routes_by_resource_name:
            active_routes = []
            for reservation in self._api.GetCurrentReservations().Reservations:
                if reservation.Id:
                    details = self._api.GetReservationDetails(reservation.Id).ReservationDescription
                    for route_info in details.ActiveRoutesInfo:
                        self._define_logical_route(reservation.Id, route_info, True)
                        active_routes.append((route_info.Source, route_info.Target))
                    for route_info in details.RequestedRoutesInfo:
                        if (route_info.Source, route_info.Target) not in active_routes:
                            self._define_logical_route(reservation.Id, route_info, False)
        return self._logical_routes_by_resource_name

    def _define_logical_route(self, reservation_id, route_info, active=True):
        source = route_info.Source
        target = route_info.Target
        route_type = route_info.RouteType
        route_alias = route_info.Alias
        shared = route_info.Shared
        logical_route = LogicalRoute(source, target, reservation_id, route_type, route_alias, active, shared)
        for segment in route_info.Segments:
            self._logical_routes_by_resource_name[segment.Source.split('/')[0]].add(logical_route)
            self._logical_routes_by_resource_name[segment.Target.split('/')[0]].add(logical_route)

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
