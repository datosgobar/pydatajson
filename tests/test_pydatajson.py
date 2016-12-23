#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests del modulo pydatajson."""

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import with_statement

from functools import wraps
import os.path
import unittest
import json
import nose
import vcr

import pydatajson

my_vcr = vcr.VCR(path_transformer=vcr.VCR.ensure_suffix('.yaml'),
                 cassette_library_dir=os.path.join("tests", "cassetes"),
                 record_mode='once')


class DataJsonTestCase(unittest.TestCase):

    SAMPLES_DIR = os.path.join("tests", "samples")
    RESULTS_DIR = os.path.join("tests", "results")
    TEMP_DIR = os.path.join("tests", "temp")

    @classmethod
    def get_sample(cls, sample_filename):
        return os.path.join(cls.SAMPLES_DIR, sample_filename)

    @classmethod
    def setUpClass(cls):
        cls.dj = pydatajson.DataJson()
        cls.maxDiff = None
        cls.longMessage = True

    @classmethod
    def tearDownClass(cls):
        del(cls.dj)

    def run_case(self, case_filename, expected_dict=None):

        sample_path = os.path.join(self.SAMPLES_DIR, case_filename + ".json")
        result_path = os.path.join(self.RESULTS_DIR, case_filename + ".json")

        expected_dict = expected_dict or json.load(open(result_path))

        response_bool = self.dj.is_valid_catalog(sample_path)
        response_dict = self.dj.validate_catalog(sample_path)

        if expected_dict["status"] == "OK":
            self.assertTrue(response_bool)
        elif expected_dict["status"] == "ERROR":
            self.assertFalse(response_bool)
        else:
            raise Exception("LA RESPUESTA {} TIENE UN status INVALIDO".format(
                case_filename))

        self.assertEqual(expected_dict, response_dict)

    def load_case_filename():

        def case_decorator(test):
            case_filename = test.__name__.split("test_validity_of_")[-1]

            @wraps(test)
            def decorated_test(*args, **kwargs):
                kwargs["case_filename"] = case_filename
                test(*args, **kwargs)

            return decorated_test

        return case_decorator

    # Tests de CAMPOS REQUERIDOS

    # Tests de inputs válidos
    @load_case_filename()
    def test_validity_of_full_data(self, case_filename):
        exp = {
            "status": "OK",
            "error": {
                "catalog": {
                    "status": "OK",
                    "errors": [],
                    "title": "Datos Argentina"
                },
                "dataset": [
                    {
                        "status": "OK",
                        "errors": [],
                        "title": "Sistema de contrataciones electrónicas"
                    }

                ]
            }
        }
        self.run_case(case_filename, exp)

    @load_case_filename()
    def test_validity_of_minimum_data(self, case_filename):
        """Un datajson con valores correctos únicamente para las claves
        requeridas."""
        self.run_case(case_filename)

    # Tests de inputs inválidos
    @load_case_filename()
    def test_validity_of_missing_catalog_title(self, case_filename):
        self.run_case(case_filename)

    @load_case_filename()
    def test_validity_of_missing_catalog_description(self, case_filename):
        self.run_case(case_filename)

    @load_case_filename()
    def test_validity_of_missing_catalog_dataset(self, case_filename):
        self.run_case(case_filename)

    @load_case_filename()
    def test_validity_of_missing_dataset_title(self, case_filename):
        self.run_case(case_filename)

    @load_case_filename()
    def test_validity_of_missing_dataset_description(self, case_filename):
        self.run_case(case_filename)

    @load_case_filename()
    def test_validity_of_missing_distribution_title(self, case_filename):
        self.run_case(case_filename)

    @load_case_filename()
    def test_validity_of_multiple_missing_descriptions(self, case_filename):
        """Datajson sin descripción de catálogo ni de su único dataset."""
        self.run_case(case_filename)

    # Tests de TIPOS DE CAMPOS

    # Tests de inputs válidos
    @load_case_filename()
    def test_validity_of_null_dataset_theme(self, case_filename):
        self.run_case(case_filename)

    @load_case_filename()
    def test_validity_of_null_field_description(self, case_filename):
        self.run_case(case_filename)

    # Tests de inputs inválidos
    @load_case_filename()
    def test_validity_of_invalid_catalog_publisher_type(self, case_filename):
        self.run_case(case_filename)

    @load_case_filename()
    def test_validity_of_invalid_publisher_mbox_format(self, case_filename):
        self.run_case(case_filename)

    @load_case_filename()
    def test_validity_of_invalid_multiple_fields_type(self, case_filename):
        """Catalog_publisher y distribution_bytesize fallan."""
        self.run_case(case_filename)

    @load_case_filename()
    def test_validity_of_invalid_dataset_theme_type(self, case_filename):
        self.run_case(case_filename)

    @load_case_filename()
    def test_validity_of_invalid_field_description_type(self, case_filename):
        self.run_case(case_filename)

    @load_case_filename()
    def test_validity_of_null_catalog_publisher(self, case_filename):
        self.run_case(case_filename)

    @load_case_filename()
    def test_validity_of_empty_mandatory_string(self, case_filename):
        """La clave requerida catalog["description"] NO puede ser str vacía."""
        self.run_case(case_filename)

    @load_case_filename()
    def test_validity_of_empty_optional_string(self, case_filename):
        """La clave opcional dataset["license"] SI puede ser str vacía."""
        self.run_case(case_filename)

    @load_case_filename()
    def test_validity_of_malformed_accrualperiodicity(self, case_filename):
        """dataset["accrualPeriodicity"] no cumple con el patrón esperado."""
        self.run_case(case_filename)

    @load_case_filename()
    def test_validity_of_malformed_date(self, case_filename):
        """catalog["issued"] no es una fecha ISO 8601 válida."""
        self.run_case(case_filename)

    @load_case_filename()
    def test_validity_of_malformed_datetime(self, case_filename):
        """catalog["issued"] no es una fecha y hora ISO 8601 válida."""
        self.run_case(case_filename)

    @load_case_filename()
    def test_validity_of_malformed_email(self, case_filename):
        """catalog["publisher"]["mbox"] no es un email válido."""
        self.run_case(case_filename)

    @load_case_filename()
    def test_validity_of_malformed_uri(self, case_filename):
        """catalog["superThemeTaxonomy"] no es una URI válida."""
        self.run_case(case_filename)

    @load_case_filename()
    def test_validity_of_invalid_dataset_type(self, case_filename):
        self.run_case(case_filename)

    @load_case_filename()
    def test_validity_of_missing_dataset(self, case_filename):
        self.run_case(case_filename)

    @load_case_filename()
    def test_validity_of_several_assorted_errors(self, case_filename):
        """Prueba que las listas con info de errores se generen correctamente
        en presencia de 7 errores de distinto tipo y jerarquía."""
        self.run_case(case_filename)

    # Tests contra una URL REMOTA
    @my_vcr.use_cassette()
    def test_validation_of_remote_datajsons(self):
        """ Testea `validate_catalog` contra dos data.json remotos."""

        # data.json remoto #1

        datajson = "http://104.131.35.253/data.json"

        res = self.dj.is_valid_catalog(datajson)
        self.assertFalse(res)

        exp = {
            "status": "ERROR",
            "error": {
                "catalog": {
                    "status": "ERROR",
                    "errors": [
                        {
                            "instance": "",
                            "validator": "format",
                            "path": [
                                "publisher",
                                "mbox"
                            ],
                            "message": "u'' is not a u'email'",
                            "error_code": 2,
                            "validator_value": "email"
                        },
                        {
                            "instance": "",
                            "validator": "minLength",
                            "path": [
                                "publisher",
                                "name"
                            ],
                            "message": "u'' is too short",
                            "error_code": 2,
                            "validator_value": 1
                        }
                    ],
                    "title": "Andino Demo"
                },
                "dataset": [
                    {
                        "status": "OK",
                        "errors": [],
                        "title": "Dataset Demo"
                    }
                ]
            }
        }

        res = self.dj.validate_catalog(datajson)
        self.assertEqual(exp, res)

        # data.json remoto #2

        datajson = "http://181.209.63.71/data.json"

        res = self.dj.is_valid_catalog(datajson)
        self.assertFalse(res)

        exp = {
            "status": "ERROR",
            "error": {
                "catalog": {
                    "status": "ERROR",
                    "errors": [
                        {
                            "instance": "",
                            "validator": "format",
                            "path": [
                                "publisher",
                                "mbox"
                            ],
                            "message": "u'' is not a u'email'",
                            "error_code": 2,
                            "validator_value": "email"
                        },
                        {
                            "instance": "",
                            "validator": "minLength",
                            "path": [
                                "publisher",
                                "name"
                            ],
                            "message": "u'' is too short",
                            "error_code": 2,
                            "validator_value": 1
                        }
                    ],
                    "title": "Andino"
                },
                "dataset": [
                    {
                        "status": "OK",
                        "errors": [],
                        "title": "Dataset Demo"
                    }
                ]
            }
        }

        res = self.dj.validate_catalog(datajson)
        self.assertEqual(exp, res)

    def test_correctness_of_accrualPeriodicity_regex(self):
        """Prueba que la regex de validación de
        dataset["accrualPeriodicity"] sea correcta."""

        datajson_path = "tests/samples/full_data.json"
        datajson = json.load(open(datajson_path))

        valid_values = ['R/P10Y', 'R/P4Y', 'R/P3Y', 'R/P2Y', 'R/P1Y',
                        'R/P6M', 'R/P4M', 'R/P3M', 'R/P2M', 'R/P1M',
                        'R/P0.5M', 'R/P0.33M', 'R/P1W', 'R/P0.5W',
                        'R/P0.33W', 'R/P1D', 'R/PT1H', 'R/PT1S',
                        'eventual']

        for value in valid_values:
            datajson["dataset"][0]["accrualPeriodicity"] = value
            res = self.dj.is_valid_catalog(datajson)
            self.assertTrue(res, msg=value)

        invalid_values = ['RP10Y', 'R/PY', 'R/P3', 'RR/P2Y', 'R/PnY',
                          'R/P6MT', 'R/PT', 'R/T1M', 'R/P0.M', '/P0.33M',
                          'R/P1Week', 'R/P.5W', 'R/P', 'R/T', 'R/PT1H3M',
                          'eventual ', '']

        for value in invalid_values:
            datajson["dataset"][0]["accrualPeriodicity"] = value
            res = self.dj.is_valid_catalog(datajson)
            self.assertFalse(res, msg=value)

    # TESTS DE generate_datasets_report
    @my_vcr.use_cassette()
    def test_generate_datasets_report(self):
        """Prueba que generate_datasets_report funcione correctamente aún con
        inputs "muy" inválidos."""

        catalogs = [
            os.path.join(self.SAMPLES_DIR, "full_data.json"),
            os.path.join(self.SAMPLES_DIR,
                         "several_datasets_for_harvest.json"),
            "http://181.209.63.71/data.json",
            os.path.join(self.SAMPLES_DIR, "missing_dataset.json"),
            {"papa": "negra"}
        ]

        expected_report_path = os.path.join(self.RESULTS_DIR,
                                            "expected_datasets_report.csv")
        actual_report_path = os.path.join(self.TEMP_DIR,
                                          "latest_datasets_report.csv")

        self.dj.generate_datasets_report(catalogs, actual_report_path)

        with open(expected_report_path) as expected:
            expected_str = expected.read()

        with open(actual_report_path) as actual:
            actual_str = actual.read()

        self.assertEqual(expected_str, actual_str)

    def test_generate_harvester_config(self):
        expected_config_path = os.path.join(self.RESULTS_DIR,
                                            "expected_harvester_config.csv")
        actual_config_path = os.path.join(self.TEMP_DIR,
                                          "latest_harvester_config.csv")

        report_path = os.path.join(self.SAMPLES_DIR,
                                   "processed_datasets_report.csv")

        self.dj.generate_harvester_config(report_path, actual_config_path)

        with open(expected_config_path) as expected:
            expected_str = expected.read()

        with open(actual_config_path) as actual:
            actual_str = actual.read()

        self.assertEquals(expected_str, actual_str)

if __name__ == '__main__':
    nose.run(defaultTest=__name__)
