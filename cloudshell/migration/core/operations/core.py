from backports.functools_lru_cache import lru_cache


class Operations(object):
    def __init__(self, api, logger, configuration, dry_run=False):
        """
        :param cloudshell.api.cloudshell_api.CloudShellAPISession api:
        :param  logging.Logger logger:
        :param cloudshell.migration.config.Configuration configuration:
        :param bool dry_run:
        """
        self._api = api
        self._logger = logger
        self._configuration = configuration
        self._dry_run = dry_run

        self.__resource_details = {}

    @property
    @lru_cache()
    def _reservations(self):
        return self._api.GetCurrentReservations().Reservations

    @lru_cache()
    def _reservation_details(self, reservation_id):
        return self._api.GetReservationDetails(reservation_id, disableCache=True).ReservationDescription

    def _get_resource_details(self, resource):
        """
        :param cloudshell.migration.entities.Resource resource:
        :rtype: cloudshell.api.cloudshell_api.ResourceInfo
        """
        return self.__resource_details.get(resource, self._load_resource_details(resource))

    def _load_resource_details(self, resource):
        """
        :param cloudshell.migration.entities.Resource resource:
        :rtype: cloudshell.api.cloudshell_api.ResourceInfo
        """
        details = self._api.GetResourceDetails(resource.name)
        self.__resource_details[resource] = details
        return details

    def is_l1_resource(self, resource):
        """
        :type resource: cloudshell.migration.entities.Resource
        """
        resource_family = resource.family or self._get_resource_details(resource).ResourceFamilyName
        if resource_family in self._configuration.L1_FAMILIES:
            return True
        else:
            return False

    def add_to_reservation(self, reservation_id, resource_name):
        self._logger.debug("Adding resource {} to reservation".format(resource_name, reservation_id))
        return self._api.AddResourcesToReservation(reservation_id, [resource_name])
