#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests para las funcionalidades de el módulo 'backup'
"""

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import with_statement

from functools import wraps
import unittest
import nose
import os
import io
import json

from six import text_type

from .context import pydatajson

SAMPLES_DIR = os.path.join("tests", "samples")
RESULTS_DIR = os.path.join("tests", "results")


class BackupTestCase(unittest.TestCase):
    """Tests for backup methods."""

    @classmethod
    def get_sample(cls, sample_filename):
        return os.path.join(SAMPLES_DIR, sample_filename)

    @classmethod
    def setUp(cls):
        cls.catalog_meta = pydatajson.DataJson(
            cls.get_sample("full_data.json"))
        cls.catalog_data = pydatajson.DataJson(
            cls.get_sample("example_time_series.json"))
        cls.maxDiff = None
        cls.longMessage = True

    @classmethod
    def tearDown(cls):
        del (cls.catalog)

    def test_make_catalog_backup_metadata(self):
        json_path = os.path.join(
            RESULTS_DIR, "catalog", "example", "data.json")
        xlsx_path = os.path.join(
            RESULTS_DIR, "catalog", "example", "catalog.xlsx")

        os.remove(json_path) if os.path.exists(json_path) else None
        os.remove(xlsx_path) if os.path.exists(xlsx_path) else None

        pydatajson.backup.make_catalog_backup(
            self.catalog_meta,
            catalog_id="example", local_catalogs_dir=RESULTS_DIR,
            include_metadata=True, include_data=False)

        self.assertTrue(os.path.exists(json_path))
        self.assertTrue(os.path.exists(xlsx_path))

    def test_make_catalog_backup_data(self):
        distribution_path = os.path.join(
            RESULTS_DIR, "catalog", "example_ts", "dataset", "1",
            "distribution", "1.2", "download",
            "odg-total-millones-pesos-1960-trimestral.csv")

        os.remove(distribution_path) if os.path.exists(
            distribution_path) else None

        pydatajson.backup.make_catalog_backup(
            self.catalog_data,
            catalog_id="example_ts", local_catalogs_dir=RESULTS_DIR,
            include_metadata=True, include_data=True)

        self.assertTrue(os.path.exists(distribution_path))


if __name__ == '__main__':
    nose.run(defaultTest=__name__)
