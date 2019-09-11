#!/usr/bin/python
# -*- coding: utf-8 -*-
from abc import ABCMeta


class AssociativeItem(object):
    __metaclass__ = ABCMeta
    name = None
    address = None
    family = None
    model = None
    associated_to = None


class Resource(AssociativeItem):
    def __init__(self, name, address=None, family=None, model=None, driver=None, exist=False):
        self.name = name
        self.address = address
        self.family = family
        self.model = model
        self.driver = driver
        self.ports = []
        self.associated_logical_routes = []
        self.associated_connectors = []

        self.attributes = {}
        self.exist = exist

    def to_string(self):
        return '/'.join(resource or '*' for resource in [self.name, self.family, self.model, self.driver])

    def __str__(self):
        return self.to_string()

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def __repr__(self):
        return self.to_string()

    def __copy__(self):
        return Resource(self.name, self.address, self.family, self.model, self.driver, self.exist)


class ResourcesPair(object):
    def __init__(self, src_resource, dst_resource):
        """
        :param Resource src_resource:
        :param Resource dst_resource:
        """
        self.src_resource = src_resource
        self.dst_resource = dst_resource

    def __hash__(self):
        return hash(self.src_resource) | hash(self.dst_resource)

    def __str__(self):
        return "ResourcesPair({}=>{})".format(self.src_resource, self.dst_resource)


class Port(AssociativeItem):
    def __init__(self, name, family=None, model=None, address=None, connected_to=None, connection_weight=None):
        self.name = name
        self.family = family
        self.model = model
        self.address = address
        self.connected_to = connected_to
        self.connection_weight = connection_weight

    def to_string(self):
        return 'Port: {}=>{}'.format(self.name, self.connected_to)
        # return 'Port: {}'.format(self.name)

    def __str__(self):
        return self.to_string()

    def __repr__(self):
        return self.to_string()

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return self.name == other.name

    def __lt__(self, other):
        return self.name < other.name


class LogicalRoute(object):
    BIDI_TYPE = 'bi'

    def __init__(self, source, target, reservation_id, route_type, route_alias, active=True, shared=False,
                 blueprint=None):
        self.source = source
        self.target = target
        self.reservation_id = reservation_id
        self.route_type = route_type
        self.route_alias = route_alias
        self.active = active
        self.shared = shared
        self.blueprint = blueprint
        self.associated_ports = []

    def to_string(self):
        return 'Route({0}<->{1}, {2}, {3})'.format(self.source, self.target, self.route_type,
                                                   'Active' if self.active else 'Inactive')

    def comparable_attribute_list(self):
        attribute_list = [self.source, self.target]
        if self.route_type == self.BIDI_TYPE:
            return sorted(attribute_list)
        else:
            return attribute_list

    def __str__(self):
        return self.to_string()

    def __eq__(self, other):
        """
        :type other: LogicalRoute
        """
        if self.route_type == other.route_type:
            return self.comparable_attribute_list() == other.comparable_attribute_list()
        else:
            return False

    def __hash__(self):
        return reduce(lambda x, y: x | y, map(hash, self.comparable_attribute_list()))


class Connector(object):
    def __init__(self, source, target, reservation_id, direction, connector_type, alias, active=True, shared=False,
                 blueprint=None):
        self.source = source
        self.target = target
        self.reservation_id = reservation_id
        self.direction = direction
        self.connector_type = connector_type
        self.alias = alias
        self.active = active
        self.shared = shared
        self.blueprint = blueprint

    def to_string(self):
        return 'Connector({0}<->{1}, {2})'.format(self.source, self.target, self.connector_type)

    def __str__(self):
        return self.to_string()

    def __eq__(self, other):
        """
        :type other: LogicalRoute
        """
        return self.source == other.source and self.target == other.target

    def __hash__(self):
        return hash(self.source) | hash(self.target)
