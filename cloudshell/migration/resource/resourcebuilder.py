from copy import copy

import click

from cloudshell.migration.core.model.entities import ResourcesPair
from cloudshell.migration.exceptions import MigrationToolException
from cloudshell.migration.resource.parser import ArgumentParser


class ResourceBuilder(object):
    def __init__(self, logger, configuration, resource_operations, confirmed=False):
        """
        :type logger: logging.Logger
        :type configuration: cloudshell.migration.config.Configuration
        :type resource_operations: cloudshell.migration.operations.resource.ResourceOperations
        """
        self._logger = logger
        self._configuration = configuration
        self._resource_operations = resource_operations
        self._argument_parser = ArgumentParser(self._logger, self._resource_operations)
        self._confirmed = confirmed

    def define_resources_pairs_from_args(self, src_resources_arguments, dst_resources_arguments):
        src_resources = self._argument_parser.initialize_existing_resources(src_resources_arguments)
        dst_resources = self._argument_parser.initialize_resources_with_stubs(dst_resources_arguments)
        return self._initialize_resources_pairs(src_resources, dst_resources)

    def _initialize_resources_pairs(self, src_resources, dst_resources):
        """
        :type src_resources: list
        :type dst_resources: list
        """

        if len(src_resources) < len(dst_resources):
            raise MigrationToolException('Number of DST resources cannot be more then number of SRC resources')

        resources_pairs = []
        for index in xrange(len(src_resources)):
            src = src_resources[index]
            if index < len(dst_resources):
                dst = dst_resources[index]
            else:
                dst = copy(dst_resources[-1])
                dst_resources.append(dst)
            pair = ResourcesPair(src, dst)
            resources_pairs.append(pair)

        for pair in resources_pairs:
            self._synchronize_resources_pair(pair)
            self._validate_resources_pair(pair)
            self._load_resources_pair(pair)

        return resources_pairs

    def _synchronize_resources_pair(self, resources_pair):
        """
        :param cloudshell.migration.core.entities.ResourcesPair resources_pair:
        :return:
        """
        src, dst = resources_pair

        # Create DST if not exist
        if not dst.exist:
            self._resource_operations.update_details(src)
            if not dst.name:
                dst.name = self._configuration.resource_name_prefix + src.name
            dst.address = src.address
            self._resource_operations.create_resource(dst)
            click.echo("Creating resource {}".format(str(dst)))
            if not self._confirmed and not click.confirm('Do you want to continue?'):
                raise click.ClickException('Aborted.')

            # Sync attributes
            self._resource_operations.load_resource_attributes(src)
            self._resource_operations.load_resource_attributes(dst)
            for name, src_attr in src.attributes.items():
                dst_attr = dst.attributes.get(name)
                if dst_attr:
                    dst_attr.Value = src_attr.Value
                    self._logger.debug("Sync attribute value: {} -> {}".format(src_attr.Name, dst_attr.Name))
                else:
                    self._logger.debug("Cannot find attribute name {} for src attr {}".format(name, src_attr.Name))
            self._resource_operations.set_resource_attributes(dst)

        return resources_pair

    def _validate_resources_pair(self, resources_pair, handled_resources=[]):
        """
        :param cloudshell.migration.core.entities.ResourcesPair resources_pair:
        :param list handled_resources:
        :return:
        """
        src = resources_pair.src_resource
        dst = resources_pair.dst_resource

        if src.name == dst.name:
            raise MigrationToolException('SRC and DST resources cannot have the same name {}'.format(src.name))
        if not src.exist:
            raise MigrationToolException('SRC resource {} does not exist'.format(src.name))

        if not dst.exist:
            if dst.name in [resource.name for resource in
                            self._resource_operations.sorted_by_family_model_resources.get((dst.family, dst.model),
                                                                                           [])]:
                raise MigrationToolException('Resource with name {} already exist'.format(dst.name))
        for resource in [src, dst]:
            if resource.name in handled_resources:
                raise MigrationToolException(
                    'Resource with name {} already used in another migration pair'.format(resource.name))
            else:
                handled_resources.append(resource.name)
        return resources_pair

    def _load_resources_pair(self, resources_pair):
        """
        :param cloudshell.migration.core.entities.ResourcesPair resources_pair:
        """
        src = resources_pair.src_resource
        dst = resources_pair.dst_resource

        # # Load SRC resource
        # if not src.ports:
        #     self._resource_operations.load_resource_ports(src)
        #     self._logical_route_operations.load_logical_routes(src)

        # Load DST resource
        if not dst.exist:
            self._resource_operations.autoload_resource(dst)
        else:
            self._resource_operations.sync_from_device(dst)
            # pass

        for resource in [src, dst]:
            if not resource.ports:
                self._resource_operations.load_resource_ports(resource)
        return resources_pair
