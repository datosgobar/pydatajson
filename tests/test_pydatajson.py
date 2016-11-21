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
        pass

    def tearDown(self):
        pass

    def test_is_valid_structure_full(self):
        """Testea estructura de data.json completo bien formado."""
        pass

    def test_is_valid_structure_required_fields(self):
        """Testea estructura de data.json (sólo campos obligatorios)."""

        dj = pydatajson.DataJson("samples/minimum_data.json")
        res = dj.is_valid_structure()
        self.assertTrue(res)

        dj = pydatajson.DataJson("samples/empty_minimum_data.json")
        res = dj.is_valid_structure()
        self.assertTrue(res)


if __name__ == '__main__':
    nose.run(defaultTest=__name__)
