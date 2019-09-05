#!/usr/bin/python
# -*- coding: utf-8 -*-
import click


class MigrationToolException(click.ClickException):
    pass


class AssociationException(MigrationToolException):
    pass
