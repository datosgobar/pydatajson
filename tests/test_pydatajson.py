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

    def test_is_valid_structure(self):
        dj_valid = pydatajson.DataJson("samples/valid_data.json")
        dj_not_valid = pydatajson.DataJson(
            "samples/not_valid_data.json")
        pass


if __name__ == '__main__':
    nose.run(defaultTest=__name__)
