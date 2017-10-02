#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests del modulo pydatajson."""

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import with_statement

import os.path
import unittest
import nose
from .context import pydatajson
from pydatajson.documentation import field_to_markdown


class DocumentationTestCase(unittest.TestCase):

    SAMPLES_DIR = os.path.join("tests", "samples")
    RESULTS_DIR = os.path.join("tests", "results")

    def test_field_to_markdown(self):
        field = {
            "title": "procedimiento_id",
            "type": "integer",
            "description": "Identificador único del procedimiento"
        }

        result = field_to_markdown(field)
        expected = "**procedimiento_id** (integer): Identificador único del procedimiento"
        self.assertEqual(result, expected)

        # elimino campos
        field.pop("type")
        result = field_to_markdown(field)
        expected = "**procedimiento_id**: Identificador único del procedimiento"
        self.assertEqual(result, expected)

        field.pop("description")
        result = field_to_markdown(field)
        expected = "**procedimiento_id**"
        self.assertEqual(result, expected)


if __name__ == '__main__':
    nose.run(defaultTest=__name__)
