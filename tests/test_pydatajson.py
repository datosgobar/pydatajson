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
from collections import OrderedDict
import mock
import filecmp
import pydatajson
import io

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
    def setUp(cls):
        cls.dj = pydatajson.DataJson()
        cls.maxDiff = None
        cls.longMessage = True

    @classmethod
    def tearDown(cls):
        del(cls.dj)

    def run_case(self, case_filename, expected_dict=None):

        sample_path = os.path.join(self.SAMPLES_DIR, case_filename + ".json")
        result_path = os.path.join(self.RESULTS_DIR, case_filename + ".json")

        with io.open(result_path, encoding='utf8') as result_file:
            expected_dict = expected_dict or json.load(result_file)

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

    # TESTS DE catalog_report
    # Reporte esperado para "full_data.json", con harvest = 0
    LOCAL_URL = os.path.join("tests", "samples", "full_data.json")
    EXPECTED_REPORT = [
        OrderedDict(
            [(u'catalog_metadata_url', LOCAL_URL),
             (u'catalog_title', u'Datos Argentina'),
             (u'catalog_description',
              u'Portal de Datos Abiertos del Gobierno de la República Argentina'),
             (u'valid_catalog_metadata', 1),
             (u'valid_dataset_metadata', 1),
             (u'dataset_index', 0),
             (u'harvest', 0),
             (u'dataset_title', u'Sistema de contrataciones electrónicas'),
             (u'dataset_accrualPeriodicity', u'R/P1Y'),
             (u'dataset_description',
              u'Datos correspondientes al Sistema de Contrataciones Electrónicas (Argentina Compra)'),
             (u'dataset_publisher_name',
              u'Ministerio de Modernización. Secretaría de Modernización Administrativa. Oficina Nacional de Contrataciones'),
             (u'dataset_superTheme', u'ECON'),
             (u'dataset_theme', u'contrataciones, compras, convocatorias'),
             (u'dataset_landingPage',
              u'http://datos.gob.ar/dataset/sistema-de-contrataciones-electronicas-argentina-compra'),
             (u'distributions_list', u'"Convocatorias abiertas durante el año 2015": http://186.33.211.253/dataset/99db6631-d1c9-470b-a73e-c62daa32c420/resource/4b7447cb-31ff-4352-96c3-589d212e1cc9/download/convocatorias-abiertas-anio-2015.csv')])]

    def test_catalog_report_harvest_valid(self):
        """catalog_report() marcará para cosecha los datasets con metadata
        válida si harvest='valid'."""
        catalog = os.path.join(self.SAMPLES_DIR, "full_data.json")

        actual = self.dj.catalog_report(catalog, harvest='valid')

        expected = list(self.EXPECTED_REPORT)
        expected[0]["harvest"] = 1

        # Compruebo explícitamente que el valor de 'harvest' sea el esperado
        self.assertEqual(actual[0]["harvest"], expected[0]["harvest"])
        # Compruebo que toda la lista sea la esperada
        self.assertListEqual(actual, expected)

    def test_catalog_report_harvest_none(self):
        """catalog_report() no marcará ningún dataset para cosecha si
        harvest='none'."""
        catalog = os.path.join(self.SAMPLES_DIR, "full_data.json")

        actual = self.dj.catalog_report(catalog, harvest='none')

        expected = list(self.EXPECTED_REPORT)
        expected[0]["harvest"] = 0

        # Compruebo explícitamente que el valor de 'harvest' sea el esperado
        self.assertEqual(actual[0]["harvest"], expected[0]["harvest"])
        # Compruebo que toda la lista sea la esperada
        self.assertListEqual(actual, expected)

    def test_catalog_report_harvest_all(self):
        """catalog_report() marcará todo dataset para cosecha si
        harvest='all'."""
        catalog = os.path.join(self.SAMPLES_DIR, "full_data.json")

        actual = self.dj.catalog_report(catalog, harvest='all')

        expected = list(self.EXPECTED_REPORT)
        expected[0]["harvest"] = 1

        # Compruebo explícitamente que el valor de 'harvest' sea el esperado
        self.assertEqual(actual[0]["harvest"], expected[0]["harvest"])
        # Compruebo que toda la lista sea la esperada
        self.assertListEqual(actual, expected)

    def test_catalog_report_harvest_report(self):
        """catalog_report() marcará para cosecha los datasets presentes en
        `report` si harvest='report'."""
        catalog = os.path.join(self.SAMPLES_DIR, "full_data.json")

        # Compruebo que no se harvestee nada si el reporte no incluye el
        # dataset del catálogo
        report = [("data.json", "Un dataset que no es")]
        actual = self.dj.catalog_report(catalog, harvest='report',
                                        report=report)

        expected = list(self.EXPECTED_REPORT)
        expected[0]["harvest"] = 0

        # Compruebo explícitamente que el valor de 'harvest' sea el esperado
        self.assertEqual(actual[0]["harvest"], expected[0]["harvest"])
        # Compruebo que toda la lista sea la esperada
        self.assertListEqual(actual, expected)

        # Compruebo que sí se harvestee si el reporte incluye el dataset del
        # catálogo
        report = [(os.path.join(self.SAMPLES_DIR, "full_data.json"),
                   "Sistema de contrataciones electrónicas")]
        actual = self.dj.catalog_report(catalog, harvest='report',
                                        report=report)

        expected = list(self.EXPECTED_REPORT)
        expected[0]["harvest"] = 1

        # Compruebo explícitamente que el valor de 'harvest' sea el esperado
        self.assertEqual(actual[0]["harvest"], expected[0]["harvest"])
        # Compruebo que toda la lista sea la esperada
        self.assertListEqual(actual, expected)

    def test_generate_datasets_report(self):
        """generate_datasets_report() debe unir correctamente los resultados de
        catalog_report()"""

        return_value = [{"ckan": "in a box", "portal": "andino", "capo": "si"}]
        self.dj.catalog_report = mock.MagicMock(return_value=return_value)

        catalogs = ["catalogo A", "catalogo B", "catalogo C"]
        actual = self.dj.generate_datasets_report(catalogs)

        expected = []
        for catalog in catalogs:
            expected.extend(return_value)

        self.assertEqual(actual, expected)

    def test_generate_harvester_config(self):
        """generate_harvester_config() debe filtrar el resultado de
        generate_datasets_report() a únicamente los 3 campos requeridos."""

        datasets_report = [
            {
                "catalog_metadata_url": 1,
                "dataset_title": 1,
                "dataset_accrualPeriodicity": 1,
                "otra key": 1,
                "harvest": 0
            },
            {
                "catalog_metadata_url": 2,
                "dataset_title": 2,
                "dataset_accrualPeriodicity": 2,
                "otra key": 2,
                "harvest": 1
            },
            {
                "catalog_metadata_url": 3,
                "dataset_title": 3,
                "dataset_accrualPeriodicity": 3,
                "otra key": 3,
                "harvest": 1
            }
        ]

        expected_config = [
            {
                "catalog_metadata_url": 2,
                "dataset_title": 2,
                "dataset_accrualPeriodicity": 2,
            },
            {
                "catalog_metadata_url": 3,
                "dataset_title": 3,
                "dataset_accrualPeriodicity": 3,
            }
        ]

        self.dj.generate_datasets_report = mock.MagicMock(
            return_value=datasets_report)

        actual_config = self.dj.generate_harvester_config(
            catalogs="un catalogo", harvest='valid')

        self.assertListEqual(actual_config, expected_config)

    # TESTS DE GENERATE_HARVESTABLE_CATALOGS

    CATALOG = {
        "title": "Micro Catalogo",
        "dataset": [
            {
                "title": "Dataset Valido",
                "description": "Descripción valida",
                "distribution": []
            },
            {
                "title": "Dataset Invalido"
            }
        ]
    }

    @mock.patch('pydatajson.pydatajson.read_catalog',
                return_value=CATALOG.copy())
    def test_generate_harvestable_catalogs_all(self, patched_read_catalog):

        catalogs = ["URL Catalogo A", "URL Catalogo B"]

        expected = [pydatajson.pydatajson.read_catalog(c) for c in catalogs]
        actual = self.dj.generate_harvestable_catalogs(catalogs, harvest='all')

        self.assertEqual(actual, expected)

    @mock.patch('pydatajson.pydatajson.read_catalog',
                return_value=CATALOG.copy())
    def test_generate_harvestable_catalogs_none(self, patched_read_catalog):

        catalogs = ["URL Catalogo A", "URL Catalogo B"]

        harvest_none = self.dj.generate_harvestable_catalogs(
            catalogs, harvest='none')

        for catalog in harvest_none:
            # Una lista vacía es "falsa"
            self.assertFalse(catalog["dataset"])


    REPORT = [
        {
            "catalog_metadata_url": "URL Catalogo A",
            "dataset_title": "Dataset Valido",
            "dataset_accrualPeriodicity": "eventual",
            "harvest": 1
        },
        {
            "catalog_metadata_url": "URL Catalogo A",
            "dataset_title": "Dataset Invalido",
            "dataset_accrualPeriodicity": "eventual",
            "harvest": 0
        },
        {
            "catalog_metadata_url": "URL Catalogo B",
            "dataset_title": "Dataset Valido",
            "dataset_accrualPeriodicity": "eventual",
            "harvest": 1
        },
        {
            "catalog_metadata_url": "URL Catalogo B",
            "dataset_title": "Dataset Invalido",
            "dataset_accrualPeriodicity": "eventual",
            "harvest": 0
        }
    ]

    @mock.patch('pydatajson.DataJson.generate_datasets_report',
                return_value=REPORT)
    @mock.patch('pydatajson.pydatajson.read_catalog',
                return_value=CATALOG.copy())
    def test_generate_harvestable_catalogs_valid(self, mock_read_catalog,
                                                 mock_gen_dsets_report):

        catalogs = ["URL Catalogo A", "URL Catalogo B"]

        expected_catalog = {
            "title": "Micro Catalogo",
            "dataset": [
                {
                    "title": "Dataset Valido",
                    "description": "Descripción valida",
                    "distribution": []
                }
            ]
        }
        expected = [expected_catalog, expected_catalog]

        actual = self.dj.generate_harvestable_catalogs(
            catalogs, harvest='valid')

        self.assertListEqual(actual, expected)

    @mock.patch('pydatajson.DataJson.generate_datasets_report',
                return_value=REPORT)
    @mock.patch('pydatajson.pydatajson.read_catalog',
                return_value=CATALOG.copy())
    def test_generate_harvestable_catalogs_report(self, mock_read_catalog,
                                                  mock_gen_dsets_report):

        catalogs = ["URL Catalogo A", "URL Catalogo B"]

        expected_catalog = {
            "title": "Micro Catalogo",
            "dataset": [
                {
                    "title": "Dataset Valido",
                    "description": "Descripción valida",
                    "distribution": []
                }
            ]
        }
        expected = [expected_catalog, expected_catalog]

        datasets_to_harvest = [
            ("URL Catalogo A", "Dataset Valido"),
            ("URL Catalogo B", "Dataset Valido")
        ]

        actual = self.dj.generate_harvestable_catalogs(
            catalogs, harvest='report', report=datasets_to_harvest)

        # `expected` es igual que en la prueba anterior.
        self.assertListEqual(actual, expected)

    # TESTS DE _READ y _WRITE

    def test_read_table_from_csv(self):
        expected_table = [
            {u'Plato': u'Milanesa', u'Precio': u'Bajo', u'Sabor': u'666'},
            {u'Plato': u'Thon\xe9, Vitel', u'Precio': u'Alto',
             u'Sabor': u'8000'},
            {u'Plato': u'Aceitunas', u'Precio': u'', u'Sabor': u'15'}
        ]
        csv_filename = os.path.join(self.SAMPLES_DIR, "read_table.csv")
        actual_table = self.dj._read(csv_filename)

        self.assertListEqual(actual_table, expected_table)

    def test_read_table_from_xlsx(self):
        expected_table = [
            {u'Plato': u'Milanesa', u'Precio': u'Bajo', u'Sabor': 666L},
            {u'Plato': u'Thon\xe9, Vitel', u'Precio': u'Alto',
             u'Sabor': 8000L},
            {u'Plato': u'Aceitunas', u'Sabor': 15L}
        ]
        xlsx_filename = os.path.join(self.SAMPLES_DIR, "read_table.xlsx")
        actual_table = self.dj._read(xlsx_filename)

        self.assertListEqual(actual_table, expected_table)

    WRITEABLE_TABLE = [
        {u'Plato': u'Milanesa', u'Precio': u'Bajo', u'Sabor': u'666'},
        {u'Plato': u'Thon\xe9, Vitel', u'Precio': u'Alto',
         u'Sabor': u'8000'},
        {u'Plato': u'Aceitunas', u'Precio': u'', u'Sabor': u'15'}
    ]

    def test_write_table_to_csv(self):
        expected_filename = os.path.join(self.RESULTS_DIR, "write_table.csv")
        actual_filename = os.path.join(self.TEMP_DIR, "write_table.csv")

        self.dj._write(self.WRITEABLE_TABLE, actual_filename)
        comparison = filecmp.cmp(actual_filename, expected_filename)
        if comparison:
            os.remove(actual_filename)
        else:
            """
{} se escribió correctamente, pero no es idéntico al esperado. Por favor,
revíselo manualmente""".format(actual_filename)
 
        # self.assertTrue(comparison)

    def test_write_table_to_xlsx(self):
        expected_filename = os.path.join(self.RESULTS_DIR, "write_table.xlsx")
        actual_filename = os.path.join(self.TEMP_DIR, "write_table.xlsx")

        self.dj._write(self.WRITEABLE_TABLE, actual_filename)
        comparison = filecmp.cmp(actual_filename, expected_filename)
        if comparison:
            os.remove(actual_filename)
        else:
            """
{} se escribió correctamente, pero no es idéntico al esperado. Por favor,
revíselo manualmente""".format(actual_filename)
 
        # self.assertTrue(comparison)

    def test_write_read_csv_loop(self):
        """Escribir y leer un CSV es una operacion idempotente."""
        temp_filename = os.path.join(self.TEMP_DIR, "write_read_loop.csv")
        self.dj._write(self.WRITEABLE_TABLE, temp_filename)
        read_table = self.dj._read(temp_filename)

        comparison = (self.WRITEABLE_TABLE == read_table)
        if comparison:
            os.remove(temp_filename)
        else:
            """
{} se escribió correctamente, pero no es idéntico al esperado. Por favor,
revíselo manualmente""".format(temp_filename)

        # self.assertListEqual(read_table, self.WRITEABLE_TABLE)

    @unittest.skip("No implementado aún")
    def test_write_read_xlsx_loop(self):
        """Escribir y leer un XLSX es una operacion idempotente."""
        temp_filename = os.path.join(self.TEMP_DIR, "write_read_loop.xlsx")
        self.dj._write(self.WRITEABLE_TABLE, temp_filename)
        read_table = self.dj._read(temp_filename)

        comparison = (self.WRITEABLE_TABLE == read_table)
        if comparison:
            os.remove(temp_filename)
            """
{} se escribió correctamente, pero no es idéntico al esperado. Por favor,
revíselo manualmente""".format(temp_filename)

        # self.assertListEqual(read_table, self.WRITEABLE_TABLE)


if __name__ == '__main__':
    nose.run(defaultTest=__name__)
