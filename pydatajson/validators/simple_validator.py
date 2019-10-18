#!/usr/bin/env python
# -*- coding: utf-8 -*-


class SimpleValidator(object):

    def __init__(self, catalog):
        self.catalog = catalog

    def validate(self):
        raise NotImplementedError
