#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests del modulo pydatajson."""

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import with_statement

import os.path
import unittest
import nose
import vcr

import pydatajson

my_vcr = vcr.VCR(path_transformer=vcr.VCR.ensure_suffix('.yaml'),
                 cassette_library_dir=os.path.join("tests", "cassetes"),
                 record_mode='new_episodes')


class DataJsonTestCase(unittest.TestCase):

    SAMPLES_DIR = os.path.join("tests", "samples")

    @classmethod
    def get_sample(cls, sample_filename):
        return os.path.join(cls.SAMPLES_DIR, sample_filename)

    def setUp(self):
        self.dj = pydatajson.DataJson()
        self.maxDiff = None

    def tearDown(self):
        del(self.dj)

    def test_is_valid_catalog_full(self):
        """Testea estructura de data.json completo bien formado."""

        res = self.dj.is_valid_catalog(self.get_sample("full_data.json"))
        self.assertTrue(res)

    def test_is_valid_catalog_required_fields(self):
        """ Estructura de data.json que sólo contiene campos obligatorios)."""

        res = self.dj.is_valid_catalog(self.get_sample("minimum_data.json"))
        self.assertTrue(res)

        res = self.dj.is_valid_catalog(
            self.get_sample("empty_minimum_data.json"))
        self.assertTrue(res)

    def test_is_valid_catalog_missing_catalog_title(self):
        """Estructura de data.json en el que un catálogo no tiene título."""

        res = self.dj.is_valid_catalog(
            self.get_sample("missing_catalog_title_data.json"))
        self.assertFalse(res)

    def test_is_valid_catalog_missing_dataset_title(self):
        """Estructura de data.json en el que un dataset no tiene título."""

        res = self.dj.is_valid_catalog(
            self.get_sample("missing_dataset_title_data.json"))
        self.assertFalse(res)

    def test_is_valid_catalog_missing_distribution_title(self):
        """Estructura de data.json en el que un recurso no tiene título."""

        res = self.dj.is_valid_catalog(
            self.get_sample("missing_distribution_title_data.json"))
        self.assertFalse(res)

    def test_validate_catalog_full_data(self):
        """ Testea `validate_catalog` contra un data.json bien formado."""

        exp = {
            "status": "OK",
            "error": {
                "catalog": {
                    "status": "OK",
                    "title": "Datos Argentina"
                },
                "dataset": [
                    {
                        "status": "OK",
                        "title": "Sistema de contrataciones electrónicas"
                    }

                ]
            }
        }

        datajson = self.get_sample("full_data.json")
        res = self.dj.validate_catalog(datajson)
        self.assertEqual(exp, res)

    def test_validate_catalog_missing_catalog_description(self):
        """ Testea `validate_catalog` contra un data.json sin descripción de
        catálogo."""

        exp = {
            "status": "ERROR",
            "error": {
                "catalog": {
                    "status": "ERROR",
                    "title": "Título del Catálogo 1"
                },
                "dataset": [
                    {
                        "status": "OK",
                        "title": "Título del Dataset 1"
                    },
                    {
                        "status": "OK",
                        "title": "Título del Dataset 2"
                    }
                ]
            }
        }

        datajson = self.get_sample("missing_catalog_description_data.json")
        res = self.dj.validate_catalog(datajson)
        self.assertEqual(exp, res)

    def test_validate_catalog_missing_dataset_description(self):
        """ Testea `validate_catalog` contra un data.json sin descripción de
        dataset."""

        exp = {
            "status": "ERROR",
            "error": {
                "catalog": {
                    "status": "OK",
                    "title": "Título del Catálogo 1"
                },
                "dataset": [
                    {
                        "status": "ERROR",
                        "title": "Título del Dataset 1"
                    },
                    {
                        "status": "OK",
                        "title": "Título del Dataset 2"
                    }
                ]
            }
        }

        datajson = self.get_sample("missing_dataset_description_data.json")
        res = self.dj.validate_catalog(datajson)
        self.assertEqual(exp, res)

    def test_validate_catalog_multiple_missing_descriptions(self):
        """ Testea `validate_catalog` contra un data.json sin descripción de
        catálogo ni datasets (2)."""

        exp = {
            "status": "ERROR",
            "error": {
                "catalog": {
                    "status": "ERROR",
                    "title": "Título del Catálogo 1"
                },
                "dataset": [
                    {
                        "status": "ERROR",
                        "title": "Título del Dataset 1"
                    },
                    {
                        "status": "ERROR",
                        "title": "Título del Dataset 2"
                    }
                ]
            }
        }

        datajson = self.get_sample("multiple_missing_descriptions_data.json")
        res = self.dj.validate_catalog(datajson)
        self.assertEqual(exp, res)

    def test_validate_catalog_missing_distribution_title(self):
        """ Testea `validate_catalog` contra un data.json sin título en una
        distribución."""

        exp = {
            "status": "ERROR",
            "error": {
                "catalog": {
                    "status": "OK",
                    "title": ""
                },
                "dataset": [
                    {
                        "status": "ERROR",
                        "title": ""
                    }
                ]
            }
        }

        datajson = self.get_sample("missing_distribution_title_data.json")
        res = self.dj.validate_catalog(datajson)
        self.assertEqual(exp, res)

    def test_validate_catalog_missing_dataset_title(self):
        """ Testea `validate_catalog` contra un data.json sin título en un
        dataset."""

        exp = {
            "status": "ERROR",
            "error": {
                "catalog": {
                    "status": "OK",
                    "title": ""
                },
                "dataset": [
                    {
                        "status": "ERROR",
                        "title": None
                    }
                ]
            }
        }

        datajson = self.get_sample("missing_dataset_title_data.json")
        res = self.dj.validate_catalog(datajson)
        self.assertEqual(exp, res)

    def test_validate_catalog_missing_catalog_title(self):
        """ Testea `validate_catalog` contra un data.json sin título de
        catálogo."""

        exp = {
            "status": "ERROR",
            "error": {
                "catalog": {
                    "status": "ERROR",
                    "title": None
                },
                "dataset": [
                    {
                        "status": "OK",
                        "title": ""
                    }
                ]
            }
        }

        datajson = self.get_sample("missing_catalog_title_data.json")
        res = self.dj.validate_catalog(datajson)
        self.assertEqual(exp, res)

    @my_vcr.use_cassette()
    def test_validate_catalog_remote_datajson(self):
        """ Testea `validate_catalog` contra dos data.json remotos."""

        exp = {
            "status": "OK",
            "error": {
                "catalog": {
                    "status": "OK",
                    "title": "Andino Demo"
                },
                "dataset": [
                    {
                        "status": "OK",
                        "title": "Dataset Demo"
                    }
                ]
            }
        }

        datajson = "http://104.131.35.253/data.json"
        res = self.dj.validate_catalog(datajson)
        self.assertEqual(exp, res)

        exp = {
            "status": "OK",
            "error": {
                "catalog": {
                    "status": "OK",
                    "title": "Andino"
                },
                "dataset": [
                    {
                        "status": "OK",
                        "title": "Dataset Demo"
                    }
                ]
            }
        }

        datajson = "http://181.209.63.71/data.json"
        res = self.dj.validate_catalog(datajson)
        self.assertEqual(exp, res)


if __name__ == '__main__':
    nose.run(defaultTest=__name__)
