from collections import defaultdict

from cloudshell.layer_one.migration_tool.entities.logical_route import LogicalRoute


class LogicalRouteHelper(object):
    def __init__(self, api, logger):
        """
        :type api: cloudshell.api.cloudshell_api.CloudShellAPISession
        :type logger: cloudshell.layer_one.migration_tool.helpers.logger.Logger
        """
        self._api = api
        self._logger = logger
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
            for reservation in self._api.GetCurrentReservations().Reservations:
                if reservation.Id:
                    details = self._api.GetReservationDetails(reservation.Id).ReservationDescription
                    for route_info in details.ActiveRoutesInfo:
                        source = route_info.Source
                        target = route_info.Target
                        logical_route = LogicalRoute(source, target, reservation.Id)
                        for segment in route_info.Segments:
                            self._logical_routes_by_resource_name[segment.Source.split('/')[0]].add(logical_route)
                            self._logical_routes_by_resource_name[segment.Target.split('/')[0]].add(logical_route)
        return self._logical_routes_by_resource_name

    def remove_route(self, logical_route):
        """
        :type logical_route: cloudshell.layer_one.migration_tool.entities.logical_route.LogicalRoute
        """
        self._logger.debug('Removing logical route {}'.format(logical_route))
        self._api.RemoveRoutesFromReservation(logical_route.reservation_id,
                                              [logical_route.source, logical_route.target], 'bi')

    def create_route(self, logical_route):
        """
        :type logical_route: cloudshell.layer_one.migration_tool.entities.logical_route.LogicalRoute
        """
        self._logger.debug('Creating logical route {}'.format(logical_route))
        self._api.CreateRouteInReservation(logical_route.reservation_id, logical_route.source, logical_route.target,
                                           False, 'bi', 2, '', False)

    def get_logical_routes_for_connection(self, connections):
        """
        :type connections: list
        """
        logical_routes = []
        for connection in connections:
            logical_route = self.logical_routes_by_segments.get(connection.port.name)
            if logical_route:
                logical_route.connections.append(connection)
                if logical_route not in logical_routes:
                    logical_routes.append(logical_route)
        return logical_routes
