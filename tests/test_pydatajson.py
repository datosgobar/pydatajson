#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests del modulo pydatajson."""

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import with_statement
import unittest
import nose
import pydatajson


class DataJsonTestCase(unittest.TestCase):

    def setUp(self):
        self.dj = pydatajson.DataJson()

    def tearDown(self):
        del(self.dj)

    def test_is_valid_catalog_full(self):
        """Testea estructura de data.json completo bien formado."""

        res = self.dj.is_valid_catalog("tests/samples/full_data.json")
        self.assertTrue(res)

    def test_is_valid_catalog_required_fields(self):
        """Testea estructura de data.json que sólo contiene campos obligatorios)."""

        res = self.dj.is_valid_catalog("tests/samples/minimum_data.json")
        self.assertTrue(res)

        res = self.dj.is_valid_catalog("tests/samples/empty_minimum_data.json")
        self.assertTrue(res)

    def test_is_valid_catalog_missing_catalog_title(self):
        """Testea estructura de data.json en el que un catálogo no tiene título."""

        res = self.dj.is_valid_catalog("tests/samples/missing_catalog_title_data.json")
        self.assertFalse(res)

    def test_is_valid_catalog_missing_dataset_title(self):
        """Testea estructura de data.json en el que un dataset no tiene título."""

        res = self.dj.is_valid_catalog("tests/samples/missing_dataset_title_data.json")
        self.assertFalse(res)

    def test_is_valid_catalog_missing_resource_tile(self):
        """Testea estructura de data.json en el que un recurso no tiene título."""

        res = self.dj.is_valid_catalog("tests/samples/missing_resource_title_data.json")
        self.assertFalse(res)



if __name__ == '__main__':
    nose.run(defaultTest=__name__)
