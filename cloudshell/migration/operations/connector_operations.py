from collections import defaultdict

from backports.functools_lru_cache import lru_cache

from cloudshell.api.cloudshell_api import SetConnectorRequest
from cloudshell.migration.entities import Connector
from cloudshell.migration.operations.operations import Operations


class ConnectorOperations(Operations):
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
