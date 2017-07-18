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
import io
from .context import pydatajson

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
    LOCAL_URL = os.path.join(SAMPLES_DIR, "full_data.json")
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

    @nose.tools.raises(ValueError)
    def test_catalog_report_harvest_report_without_report_file(self):
        """Si harvest='report' y report='None', se levanta un ValueError."""
        catalog = os.path.join(self.SAMPLES_DIR, "full_data.json")
        self.dj.catalog_report(catalog, harvest='report')

    @nose.tools.raises(ValueError)
    def test_catalog_report_invalid_harvest_value(self):
        """Si harvest not in ["all", "none", "valid", "report"] se levanta un
        ValueError."""
        catalog = os.path.join(self.SAMPLES_DIR, "full_data.json")
        self.dj.catalog_report(catalog, harvest='harvest')

    def test_catalog_report_missing_datasets(self):
        """Si la clave "dataset" de un catalogo no esta presente, el reporte es
        una tabla vacía."""
        catalog = os.path.join(self.SAMPLES_DIR, "missing_dataset.json")
        self.assertListEqual(self.dj.catalog_report(catalog), [])

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

    def test_generate_datasets_report_single_catalog(self):
        """Invocar generate_datasets_report con una str que sea la ruta a un
        catálogo, o con una lista que sólo contenga esa misma string dan el
        mismo resultado."""
        catalog_str = os.path.join(self.SAMPLES_DIR, "full_data.json")
        catalog_list = [catalog_str]

        report_str = self.dj.generate_datasets_report(catalog_str)
        report_list = self.dj.generate_datasets_report(catalog_list)

        self.assertListEqual(report_str, report_list)

    @mock.patch('pydatajson.writers.write_table')
    def test_export_generate_datasets_report(self, write_table_mock):
        """Si se pasa una ruta en `export_path`, generate_datasets_report llama
        a writers.write_table."""
        catalog = os.path.join(self.SAMPLES_DIR, "full_data.json")

        self.dj.generate_datasets_report(catalog, export_path="una ruta")

        pydatajson.writers.write_table.assert_called_once()

    def test_generate_harvester_config_freq_none(self):
        """generate_harvester_config() debe filtrar el resultado de
        generate_datasets_report() a únicamente los 3 campos requeridos, y
        conservar el accrualPeriodicity original."""

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
            catalogs="un catalogo", harvest='valid', frequency=None)

        self.assertListEqual(actual_config, expected_config)

    def test_generate_harvester_config_no_freq(self):
        """generate_harvester_config() debe filtrar el resultado de
        generate_datasets_report() a únicamente los 3 campos requeridos, y
        usar "R/P1D" como accrualPeriodicity"""

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
                "dataset_accrualPeriodicity": "R/P1D",
            },
            {
                "catalog_metadata_url": 3,
                "dataset_title": 3,
                "dataset_accrualPeriodicity": "R/P1D",
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

    @mock.patch('pydatajson.readers.read_catalog',
                return_value=CATALOG.copy())
    def test_generate_harvestable_catalogs_all(self, patched_read_catalog):

        catalogs = ["URL Catalogo A", "URL Catalogo B"]

        expected = [pydatajson.readers.read_catalog(c) for c in catalogs]
        actual = self.dj.generate_harvestable_catalogs(catalogs, harvest='all')

        self.assertEqual(actual, expected)

    @mock.patch('pydatajson.readers.read_catalog',
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
    @mock.patch('pydatajson.readers.read_catalog',
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
    @mock.patch('pydatajson.readers.read_catalog',
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

    def test_generate_datasets_summary(self):
        """Genera informe conciso sobre datasets correctamente."""
        catalog = os.path.join(self.SAMPLES_DIR,
                               "several_datasets_for_harvest.json")
        actual = self.dj.generate_datasets_summary(catalog)
        expected = [
            OrderedDict([('indice', 0),
                         ('titulo', 'Sistema de contrataciones electrónicas UNO'),
                         ('identificador', None),
                         ('estado_metadatos', 'ERROR'),
                         ('cant_errores', 4),
                         ('cant_distribuciones', 4)]),
            OrderedDict([('indice', 1),
                         ('titulo', 'Sistema de contrataciones electrónicas DOS'),
                         ('identificador', None),
                         ('estado_metadatos', 'OK'),
                         ('cant_errores', 0),
                         ('cant_distribuciones', 1)]),
            OrderedDict([('indice', 2),
                         ('titulo', 'Sistema de contrataciones electrónicas TRES'),
                         ('identificador', None),
                         ('estado_metadatos', 'OK'),
                         ('cant_errores', 0),
                         ('cant_distribuciones', 1)])]

        self.assertListEqual(actual, expected)

    def test_generate_catalog_readme(self):
        """Genera README para presentar un catálogo."""
        catalog = os.path.join(self.SAMPLES_DIR,
                               "several_datasets_for_harvest.json")
        actual_filename = os.path.join(self.TEMP_DIR, "catalog_readme.md")

        expected_filename = os.path.join(self.RESULTS_DIR, "catalog_readme.md")

        self.dj.generate_catalog_readme(catalog, export_path=actual_filename)

        comparison = filecmp.cmp(actual_filename, expected_filename)
        if comparison:
            os.remove(actual_filename)
        else:
            """
{} se escribió correctamente, pero no es idéntico al esperado. Por favor,
revíselo manualmente""".format(actual_filename)

        self.assertTrue(comparison)

    def test_generate_catalog_indicators(self):
        catalog = os.path.join(self.SAMPLES_DIR, "several_datasets.json")

        indicators = self.dj.generate_catalogs_indicators(catalog)[0][0]

        # Resultados esperados haciendo cuentas manuales sobre el catálogo
        expected = {
            'datasets_cant': 3,
            'distribuciones_cant': 6,
            'datasets_meta_ok_cant': 2,
            'datasets_meta_error_cant': 1,
            'datasets_meta_ok_pct': round(100 * float(2) / 3, 2),
        }

        for k, v in expected.items():
            self.assertTrue(indicators[k], v)

    def test_date_indicators(self):
        from datetime import datetime
        catalog = os.path.join(self.SAMPLES_DIR, "several_datasets.json")

        indicators = self.dj.generate_catalogs_indicators(catalog)[0][0]
        dias_diff = (datetime.now() - datetime(2016, 4, 14)).days

        expected = {
            'catalogo_ultima_actualizacion_dias': dias_diff,
            'datasets_actualizados_cant': 1,
            'datasets_desactualizados_cant': 2,
            'datasets_actualizados_pct': 100 * round(float(1) / 3, 2),
            'datasets_frecuencia_cant': {
                'R/P1W': 1,
                'R/P1M': 1,
                'eventual': 1
            },
        }

        for k, v in expected.items():
            self.assertEqual(indicators[k], v)

    def test_format_indicators(self):
        catalog = os.path.join(self.SAMPLES_DIR, "several_datasets.json")

        indicators = self.dj.generate_catalogs_indicators(catalog)[0][0]

        expected = {
            'distribuciones_formatos_cant': {
                'CSV': 1,
                'XLSX': 1,
                'PDF': 1
            }
        }

        for k, v in expected.items():
            self.assertEqual(indicators[k], v)

    def test_field_indicators_on_min_catalog(self):
        catalog = os.path.join(self.SAMPLES_DIR, "minimum_data.json")

        # Se espera un único catálogo como resultado, índice 0
        indicators = self.dj.generate_catalogs_indicators(catalog)[0][0]

        expected = {
            'campos_recomendados_pct': 0.0,
            'campos_optativos_pct': 0.0,
        }

        for k, v in expected.items():
            self.assertEqual(indicators[k], v)

    def test_field_indicators_on_full_catalog(self):
        catalog = os.path.join(self.SAMPLES_DIR, "full_data.json")

        # Se espera un único catálogo como resultado, índice 0
        indicators = self.dj.generate_catalogs_indicators(catalog)[0][0]

        expected = {
            'campos_recomendados_pct': 100,
            'campos_optativos_pct': 100
        }

        for k, v in expected.items():
            self.assertEqual(indicators[k], v)

    def test_federation_indicators_same_catalog(self):
        catalog = os.path.join(self.SAMPLES_DIR, "several_datasets.json")

        indicators = self.dj.generate_catalogs_indicators(catalog, catalog)[1]

        # Esperado: todos los datasets están federados
        expected = {
            'datasets_federados_cant': 3,
            'datasets_no_federados_cant': 0,
            'datasets_no_federados': [],
            'datasets_federados_pct': 100
        }

        for k, v in expected.items():
            self.assertEqual(indicators[k], v)

    def test_federation_indicators_no_datasets(self):
        catalog = os.path.join(self.SAMPLES_DIR, "several_datasets.json")
        central = os.path.join(self.SAMPLES_DIR, "catalogo_justicia.json")
        indicators = self.dj.generate_catalogs_indicators(catalog, central)[1]

        # Esperado: ningún dataset está federado
        expected = {
            'datasets_federados_cant': 0,
            'datasets_no_federados_cant': 3,
            'datasets_no_federados': [
                ('Sistema de contrataciones electrónicas UNO', None),
                ('Sistema de contrataciones electrónicas DOS', None),
                ('Sistema de contrataciones electrónicas TRES', None)],
            'datasets_federados_pct': 0
        }

        for k, v in expected.items():
            self.assertEqual(indicators[k], v)

    def test_federation_indicators_removed_datasets(self):

        # CASO 1
        # se buscan los datasets federados en el central que fueron eliminados
        # en el específico pero no se encuentran porque el publisher.name no
        # tiene publicado ningún otro dataset en el catálogo específico
        catalog = os.path.join(
            self.SAMPLES_DIR, "catalogo_justicia_removed.json"
        )
        central = os.path.join(self.SAMPLES_DIR, "catalogo_justicia.json")
        indicators = self.dj.generate_catalogs_indicators(catalog, central)[1]

        # Esperado: no se encuentra el dataset removido, porque el
        # publisher.name no existe en ningún otro dataset
        expected = {
            "datasets_federados_eliminados_cant": 0,
            "datasets_federados_eliminados": []
        }

        for k, v in expected.items():
            self.assertEqual(indicators[k], v)

        # CASO 2
        # se buscan los datasets federados en el central que fueron eliminados
        # en el específico y se encuentran porque el publisher.name tiene
        # publicado otro dataset en el catálogo específico
        catalog = os.path.join(
            self.SAMPLES_DIR, "catalogo_justicia_removed_publisher.json"
        )
        indicators = self.dj.generate_catalogs_indicators(catalog, central)[1]
        # Esperado: no se encuentra el dataset removido, porque el
        # publisher.name no existe en ningún otro dataset
        expected = {
            "datasets_federados_eliminados_cant": 1,
            "datasets_federados_eliminados": [(
                'Base de datos legislativos Infoleg',
                "http://datos.jus.gob.ar/dataset/base-de-datos-legislativos-infoleg"
            )]
        }

        for k, v in expected.items():
            self.assertEqual(indicators[k], v)

    def test_network_indicators(self):
        one_catalog = os.path.join(self.SAMPLES_DIR, "several_datasets.json")
        other_catalog = os.path.join(self.SAMPLES_DIR, "full_data.json")

        indicators, network_indicators = self.dj.generate_catalogs_indicators([
            one_catalog,
            other_catalog
        ])

        # Esperado: suma de los indicadores individuales
        # No se testean los indicadores de actualización porque las fechas no
        # se mantienen actualizadas
        expected = {
            'catalogos_cant': 2,
            'datasets_cant': 4,
            'distribuciones_cant': 7,
            'datasets_meta_ok_cant': 3,
            'datasets_meta_error_cant': 1,
            'datasets_meta_ok_pct': 100 * float(3) / 4,
            'distribuciones_formatos_cant': {
                'CSV': 2,
                'XLSX': 1,
                'PDF': 1
            },
            'campos_optativos_pct': 21.95,
            'campos_recomendados_pct': 47.15,
        }

        for k, v in expected.items():
            self.assertEqual(network_indicators[k], v)

    def test_indicators_invalid_periodicity(self):
        catalog = os.path.join(self.SAMPLES_DIR,
                               "malformed_accrualperiodicity.json")

        indicators = self.dj.generate_catalogs_indicators(catalog)[0][0]

        # Periodicidad inválida se considera automáticamente como
        # catálogo desactualizado
        expected = {
            'datasets_actualizados_cant': 0,
            'datasets_desactualizados_cant': 1,
            'datasets_actualizados_pct': 0
        }

        for k, v in expected.items():
            self.assertEqual(indicators[k], v, k)

    def test_indicators_missing_periodicity(self):
        catalog = os.path.join(self.SAMPLES_DIR, "missing_periodicity.json")

        # Dataset con periodicidad faltante no aporta valores para indicadores
        # de tipo 'datasets_(des)actualizados'
        indicators = self.dj.generate_catalogs_indicators(catalog)[0][0]
        expected = {
            'datasets_actualizados_cant': 0,
            'datasets_desactualizados_cant': 0,
            'datasets_actualizados_pct': 0
        }

        for k, v in expected.items():
            self.assertEqual(indicators[k], v, k)

    def test_indicators_missing_dataset(self):
        catalog = os.path.join(self.SAMPLES_DIR, "missing_dataset.json")

        indicators = self.dj.generate_catalogs_indicators(catalog)[0][0]

        # Catálogo sin datasets no aporta indicadores significativos
        expected = {
            'datasets_cant': 0,
            'datasets_meta_ok_cant': 0,
            'datasets_meta_error_cant': 0,
            'datasets_actualizados_cant': 0,
            'datasets_desactualizados_cant': 0,
            'datasets_actualizados_pct': 0,
            'distribuciones_formatos_cant': {},
            'datasets_frecuencia_cant': {}
        }

        for k, v in expected.items():
            self.assertEqual(indicators[k], v, k)

    def test_last_updated_indicator_missing_issued_field(self):
        from datetime import datetime
        catalog = os.path.join(self.SAMPLES_DIR, "minimum_data.json")

        indicators = self.dj.generate_catalogs_indicators(catalog)[0][0]
        dias_diff = (datetime.now() - datetime(2016, 4, 14)).days

        # Catálogo no tiene 'issued', pero su dataset sí -> uso el del dataset
        expected = {
            'catalogo_ultima_actualizacion_dias':  dias_diff
        }

        for k, v in expected.items():
            self.assertEqual(indicators[k], v, k)

    def test_dataset_is_updated(self):
        catalog = os.path.join(self.SAMPLES_DIR, "catalogo_justicia.json")

        # Datasset con periodicity mensual vencida
        dataset = "Base de datos legislativos Infoleg"
        self.assertFalse(self.dj.dataset_is_updated(catalog, dataset))

        # Dataset con periodicity eventual, siempre True
        dataset = "Declaración Jurada Patrimonial Integral de carácter público"
        self.assertTrue(self.dj.dataset_is_updated(catalog, dataset))

    def test_parse_date_string(self):
        self.assertEqual(self.dj._parse_date_string(""), None)


if __name__ == '__main__':
    nose.run(defaultTest=__name__)
