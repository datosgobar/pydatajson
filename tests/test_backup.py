#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests para las funcionalidades de el módulo 'backup'
"""

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import with_statement

from contextlib import contextmanager

import unittest
import nose
import os
import vcr
import tempfile
import shutil


from .context import pydatajson

SAMPLES_DIR = os.path.join("tests", "samples")
RESULTS_DIR = os.path.join("tests", "results")

VCR = vcr.VCR(path_transformer=vcr.VCR.ensure_suffix('.yaml'),
              cassette_library_dir=os.path.join("tests", "cassetes", "backup"),
              record_mode='once')


@contextmanager
def tempdir(cleanup=True):
    tmp = tempfile.mkdtemp(dir='tests/temp')
    try:
        yield tmp
    finally:
        cleanup and shutil.rmtree(tmp, ignore_errors=True)


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
        del (cls.catalog_meta)
        del (cls.catalog_data)

    def test_make_catalog_backup_metadata(self):
        with tempdir() as temp_dir:
            json_path = os.path.join(
                temp_dir, "catalog", "example", "data.json")
            xlsx_path = os.path.join(
                temp_dir, "catalog", "example", "catalog.xlsx")

            pydatajson.backup.make_catalog_backup(
                self.catalog_meta,
                catalog_id="example", local_catalogs_dir=temp_dir,
                include_metadata=True, include_data=False)

            self.assertTrue(os.path.exists(json_path))
            self.assertTrue(os.path.exists(xlsx_path))

    @VCR.use_cassette()
    def test_make_catalog_backup_data(self):
        with tempdir() as temp_dir:
            distribution_path = os.path.abspath(
                os.path.join(
                    temp_dir,
                    "catalog",
                    "example_ts",
                    "dataset",
                    "1",
                    "distribution",
                    "1.2",
                    "download",
                    "oferta-demanda-globales-datos-desestacionalizados"
                    "-valores-trimestrales-base-1993.csv"))

            pydatajson.backup.make_catalog_backup(
                self.catalog_data,
                catalog_id="example_ts", local_catalogs_dir=temp_dir,
                include_metadata=True, include_data=True)

            self.assertTrue(os.path.exists(distribution_path))

    @VCR.use_cassette()
    def test_make_catalog_backup_data_without_file_name(self):
        with tempdir() as temp_dir:
            distribution_path = os.path.abspath(os.path.join(
                temp_dir, "catalog", "example_ts", "dataset", "1",
                "distribution", "1.2.b", "download",
                "odg-total-millones-pesos-1960-trimestral.csv"
            ))

            pydatajson.backup.make_catalog_backup(
                self.catalog_data,
                catalog_id="example_ts", local_catalogs_dir=temp_dir,
                include_metadata=True, include_data=True)

            self.assertTrue(os.path.exists(distribution_path))


if __name__ == '__main__':
    nose.run(defaultTest=__name__)
