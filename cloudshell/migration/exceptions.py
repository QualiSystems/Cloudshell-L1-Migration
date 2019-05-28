#!/usr/bin/python
# -*- coding: utf-8 -*-


class MigrationToolException(Exception):
    def __init__(self, message):
        self.message = message
