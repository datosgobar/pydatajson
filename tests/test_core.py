# -*- coding: utf-8 -*-

"""Tests del modulo pydatajson."""

from __future__ import print_function, unicode_literals, with_statement

import os.path
from collections import OrderedDict
from pprint import pprint

import nose
import vcr
from nose.tools import assert_true, assert_false, assert_equal
from nose.tools import assert_list_equal, assert_raises
from six import iteritems


try:
    import mock
except ImportError:
    from unittest import mock
import filecmp
from .context import pydatajson
from .support.decorators import load_expected_result, RESULTS_DIR

my_vcr = vcr.VCR(path_transformer=vcr.VCR.ensure_suffix('.yaml'),
                 cassette_library_dir=os.path.join("tests", "cassetes"),
                 record_mode='once')


class TestDataJsonTestCase(object):
    SAMPLES_DIR = os.path.join("tests", "samples")
    RESULTS_DIR = RESULTS_DIR
    TEMP_DIR = os.path.join("tests", "temp")

    @classmethod
    def get_sample(cls, sample_filename):
        return os.path.join(cls.SAMPLES_DIR, sample_filename)

    @classmethod
    def setUp(cls):
        cls.dj = pydatajson.DataJson(cls.get_sample("full_data.json"))
        cls.catalog = pydatajson.readers.read_catalog(
            cls.get_sample("full_data.json"))
        cls.maxDiff = None
        cls.longMessage = True

    @classmethod
    def tearDown(cls):
        del (cls.dj)

    # TESTS DE catalog_report
    # Reporte esperado para "full_data.json", con harvest = 0
    LOCAL_URL = os.path.join(SAMPLES_DIR, "full_data.json")
    EXPECTED_REPORT = [
        OrderedDict([
            (u'catalog_metadata_url', u'tests/samples/full_data.json'),
            (u'catalog_federation_id', u'modernizacion'),
            (u'catalog_federation_org', None),
            (u'catalog_title', u'Datos Argentina'),
            (u'catalog_description',
             u'Portal de Datos Abiertos del Gobierno '
             u'de la Rep\xfablica Argentina'),
            (u'valid_catalog_metadata', 1),
            (u'valid_dataset_metadata', 1),
            (u'dataset_index', 0),
            (u'harvest', 1),
            (u'dataset_identifier',
             u'99db6631-d1c9-470b-a73e-c62daa32c777'),
            (u'dataset_title', u'Sistema de contrataciones electr\xf3nicas'),
            (u'dataset_accrualPeriodicity', u'R/P1Y'),
            (u'dataset_description',
             u'Datos correspondientes al Sistema de '
             u'Contrataciones Electr\xf3nicas (Argentina Compra)'),
            (u'dataset_publisher_name',
             u'Ministerio de Modernizaci\xf3n. Secretar\xeda de '
             u'Modernizaci\xf3n Administrativa. '
             u'Oficina Nacional de Contrataciones'),
            (u'dataset_superTheme', u'econ'),
            (u'dataset_theme', u'contrataciones, compras, convocatorias'),
            (u'dataset_landingPage',
             u'http://datos.gob.ar/dataset/'
             u'sistema-de-contrataciones-electronicas-argentina-compra'),
            (u'dataset_landingPage_generated',
             u'dataset/99db6631-d1c9-470b-a73e-c62daa32c777'),
            (u'dataset_issued', u'2016-04-14T19:48:05.433640-03:00'),
            (u'dataset_modified', u'2016-04-19T19:48:05.433640-03:00'),
            (u'distributions_formats', '{"CSV": 1}'),
            (u'distributions_list',
             u'"Convocatorias abiertas durante el a\xf1o 2015": '
             u'http://186.33.211.253/dataset/'
             u'99db6631-d1c9-470b-a73e-c62daa32c420/resource/'
             u'4b7447cb-31ff-4352-96c3-589d212e1cc9/download/'
             u'convocatorias-abiertas-anio-2015.csv'),
            (u'dataset_license',
             u'Open Data Commons Open Database License 1.0'),
            (u'dataset_language', u'spa'),
            (u'dataset_spatial', u'ARG'),
            (u'dataset_temporal', u'2015-01-01/2015-12-31'),
            (u'notas', u'')]),

        OrderedDict([
            (u'catalog_metadata_url', u'tests/samples/full_data.json'),
            (u'catalog_federation_id', u'modernizacion'),
            (u'catalog_federation_org', None),
            (u'catalog_title', u'Datos Argentina'),
            (u'catalog_description',
             u'Portal de Datos Abiertos del Gobierno '
             u'de la Rep\xfablica Argentina'),
            (u'valid_catalog_metadata', 1),
            (u'valid_dataset_metadata', 1),
            (u'dataset_index', 1),
            (u'harvest', 1),
            (u'dataset_identifier', u'99db6631-d1c9-470b-a73e-c62daa32c420'),
            (u'dataset_title',
             u'Sistema de contrataciones electr\xf3nicas (sin datos)'),
            (u'dataset_accrualPeriodicity', u'R/P1Y'),
            (u'dataset_description',
             u'Datos correspondientes al Sistema de Contrataciones '
             u'Electr\xf3nicas (Argentina Compra) (sin datos)'),
            (u'dataset_publisher_name',
             u'Ministerio de Modernizaci\xf3n. Secretar\xeda de '
             u'Modernizaci\xf3n Administrativa. Oficina Nacional '
             u'de Contrataciones'),
            (u'dataset_superTheme', u'ECON'),
            (u'dataset_theme', u'contrataciones, compras, convocatorias'),
            (u'dataset_landingPage',
             u'http://datos.gob.ar/dataset/'
             u'sistema-de-contrataciones-electronicas-argentina-compra'),
            (u'dataset_landingPage_generated',
             u'dataset/99db6631-d1c9-470b-a73e-c62daa32c420'),
            (u'dataset_issued', u'2016-04-14T19:48:05.433640-03:00'),
            (u'dataset_modified', u'2016-04-19T19:48:05.433640-03:00'),
            (u'distributions_formats', '{"PDF": 1}'),
            (u'distributions_list',
             u'"Convocatorias abiertas durante el a\xf1o 2015": '
             u'http://186.33.211.253/dataset/'
             u'99db6631-d1c9-470b-a73e-c62daa32c420/resource/'
             u'4b7447cb-31ff-4352-96c3-589d212e1cc9/download/'
             u'convocatorias-abiertas-anio-2015.pdf'),
            (u'dataset_license',
             u'Open Data Commons Open Database License 1.0'),
            (u'dataset_language', u'spa'),
            (u'dataset_spatial', u'ARG'),
            (u'dataset_temporal', u'2015-01-01/2015-12-31'),
            (u'notas', u'No tiene distribuciones con datos.')])]

    def test_catalog_report_harvest_good(self):
        """catalog_report() marcará para cosecha los datasets con metadata
        válida si harvest='valid'."""
        catalog = os.path.join(self.SAMPLES_DIR, "full_data.json")

        actual = self.dj.catalog_report(
            catalog, harvest='good', catalog_id="modernizacion")

        expected = list(self.EXPECTED_REPORT)
        expected[0]["harvest"] = 1
        expected[1]["harvest"] = 0

        # Compruebo explícitamente que el valor de 'harvest' sea el esperado
        assert_equal(actual[0]["harvest"], expected[0]["harvest"])
        assert_equal(actual[1]["harvest"], expected[1]["harvest"])
        # Compruebo que toda la lista sea la esperada
        assert_list_equal(actual, expected)

    def test_catalog_report_harvest_valid(self):
        """catalog_report() marcará para cosecha los datasets con metadata
        válida si harvest='valid'."""
        catalog = os.path.join(self.SAMPLES_DIR, "full_data.json")

        actual = self.dj.catalog_report(
            catalog, harvest='valid', catalog_id="modernizacion")

        expected = list(self.EXPECTED_REPORT)
        expected[0]["harvest"] = 1
        expected[1]["harvest"] = 1

        # Compruebo explícitamente que el valor de 'harvest' sea el esperado
        assert_equal(actual[0]["harvest"], expected[0]["harvest"])
        # Compruebo que toda la lista sea la esperada
        print(actual)
        assert_list_equal(actual, expected)

    def test_catalog_report_harvest_none(self):
        """catalog_report() no marcará ningún dataset para cosecha si
        harvest='none'."""
        catalog = os.path.join(self.SAMPLES_DIR, "full_data.json")

        actual = self.dj.catalog_report(
            catalog, harvest='none', catalog_id="modernizacion")

        expected = list(self.EXPECTED_REPORT)
        expected[0]["harvest"] = 0
        expected[1]["harvest"] = 0

        # Compruebo explícitamente que el valor de 'harvest' sea el esperado
        assert_equal(actual[0]["harvest"], expected[0]["harvest"])
        # Compruebo que toda la lista sea la esperada
        assert_list_equal(actual, expected)

    def test_catalog_report_harvest_all(self):
        """catalog_report() marcará todo dataset para cosecha si
        harvest='all'."""
        catalog = os.path.join(self.SAMPLES_DIR, "full_data.json")

        actual = self.dj.catalog_report(
            catalog, harvest='all', catalog_id="modernizacion")

        expected = list(self.EXPECTED_REPORT)
        expected[0]["harvest"] = 1
        expected[1]["harvest"] = 1

        # Compruebo explícitamente que el valor de 'harvest' sea el esperado
        assert_equal(actual[0]["harvest"], expected[0]["harvest"])
        # Compruebo que toda la lista sea la esperada
        assert_list_equal(actual, expected)

    def test_catalog_report_harvest_report(self):
        """catalog_report() marcará para cosecha los datasets presentes en
        `report` si harvest='report'."""
        catalog = os.path.join(self.SAMPLES_DIR, "full_data.json")

        # Compruebo que no se harvestee nada si el reporte no incluye el
        # dataset del catálogo
        report = [("data.json", "Un dataset que no es")]
        actual = self.dj.catalog_report(
            catalog, harvest='report', report=report,
            catalog_id="modernizacion"
        )

        expected = list(self.EXPECTED_REPORT)
        expected[0]["harvest"] = 0
        expected[1]["harvest"] = 0

        # Compruebo explícitamente que el valor de 'harvest' sea el esperado
        assert_equal(actual[0]["harvest"], expected[0]["harvest"])
        # Compruebo que toda la lista sea la esperada
        assert_list_equal(actual, expected)

        # Compruebo que sí se harvestee si el reporte incluye el dataset del
        # catálogo
        report = [(os.path.join(self.SAMPLES_DIR, "full_data.json"),
                   "Sistema de contrataciones electrónicas")]
        actual = self.dj.catalog_report(
            catalog, harvest='report',
            report=report, catalog_id="modernizacion")

        expected = list(self.EXPECTED_REPORT)
        expected[0]["harvest"] = 1

        # Compruebo explícitamente que el valor de 'harvest' sea el esperado
        assert_equal(actual[0]["harvest"], expected[0]["harvest"])
        # Compruebo que toda la lista sea la esperada
        assert_list_equal(actual, expected)

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
        assert_list_equal(self.dj.catalog_report(catalog), [])

    def test_generate_datasets_report(self):
        """generate_datasets_report() debe unir correctamente los resultados de
        catalog_report()"""

        return_value = [{"ckan": "in a box", "portal": "andino", "capo": "si"}]
        self.dj.catalog_report = mock.MagicMock(return_value=return_value)

        catalogs = [pydatajson.DataJson(), pydatajson.DataJson(),
                    pydatajson.DataJson()]
        actual = self.dj.generate_datasets_report(catalogs)

        expected = []
        for catalog in catalogs:
            expected.extend(return_value)

        assert_equal(actual, expected)

    def test_generate_datasets_report_single_catalog(self):
        """Invocar generate_datasets_report con una str que sea la ruta a un
        catálogo, o con una lista que sólo contenga esa misma string dan el
        mismo resultado."""
        catalog_str = os.path.join(self.SAMPLES_DIR, "full_data.json")
        catalog_list = [catalog_str]

        report_str = self.dj.generate_datasets_report(catalog_str)
        report_list = self.dj.generate_datasets_report(catalog_list)

        assert_list_equal(report_str, report_list)

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
                "dataset_identifier": 1,
                "dataset_accrualPeriodicity": 1,
                "otra key": 1,
                "catalog_federation_org": "organizacion-en-ckan",
                "catalog_federation_id": "organismo",
                "harvest": 0
            },
            {
                "catalog_metadata_url": 2,
                "dataset_identifier": 2,
                "dataset_accrualPeriodicity": 2,
                "otra key": 2,
                "catalog_federation_org": "organizacion-en-ckan",
                "catalog_federation_id": "organismo",

                "harvest": 1
            },
            {
                "catalog_metadata_url": 3,
                "dataset_identifier": 3,
                "dataset_accrualPeriodicity": 3,
                "otra key": 3,
                "catalog_federation_org": "organizacion-en-ckan",
                "catalog_federation_id": "organismo",

                "harvest": 1
            }
        ]

        expected_config = [
            {
                "dataset_identifier": 2,
                "dataset_organization": "organizacion-en-ckan",
                "catalog_id": "organismo",
            },
            {
                "dataset_identifier": 3,
                "dataset_organization": "organizacion-en-ckan",
                "catalog_id": "organismo",
            }
        ]

        self.dj.generate_datasets_report = mock.MagicMock(
            return_value=datasets_report)

        actual_config = self.dj.generate_harvester_config(
            catalogs="un catalogo", harvest='valid')

        assert_list_equal(actual_config, expected_config)

    def test_generate_harvester_config_no_freq(self):
        """generate_harvester_config() debe filtrar el resultado de
        generate_datasets_report() a únicamente los 3 campos requeridos, y
        usar "R/P1D" como accrualPeriodicity"""

        datasets_report = [
            {
                "catalog_metadata_url": 1,
                "dataset_identifier": 1,
                "dataset_accrualPeriodicity": 1,
                "catalog_federation_org": "organizacion-en-ckan",
                "catalog_federation_id": "organismo",
                "otra key": 1,
                "harvest": 0
            },
            {
                "catalog_metadata_url": 2,
                "dataset_identifier": 2,
                "dataset_accrualPeriodicity": 2,
                "catalog_federation_org": "organizacion-en-ckan",
                "catalog_federation_id": "organismo",
                "otra key": 2,
                "harvest": 1
            },
            {
                "catalog_metadata_url": 3,
                "dataset_identifier": 3,
                "dataset_accrualPeriodicity": 3,
                "catalog_federation_org": "organizacion-en-ckan",
                "catalog_federation_id": "organismo",
                "otra key": 3,
                "harvest": 1
            }
        ]

        expected_config = [
            {
                "dataset_identifier": 2,
                "dataset_organization": "organizacion-en-ckan",
                "catalog_id": "organismo",
            },
            {
                "dataset_identifier": 3,
                "dataset_organization": "organizacion-en-ckan",
                "catalog_id": "organismo",
            }
        ]

        self.dj.generate_datasets_report = mock.MagicMock(
            return_value=datasets_report)

        actual_config = self.dj.generate_harvester_config(
            catalogs="un catalogo", harvest='valid')

        assert_list_equal(actual_config, expected_config)

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

        assert_equal(actual, expected)

    @mock.patch('pydatajson.readers.read_catalog',
                return_value=CATALOG.copy())
    def test_generate_harvestable_catalogs_none(self, patched_read_catalog):

        catalogs = ["URL Catalogo A", "URL Catalogo B"]

        harvest_none = self.dj.generate_harvestable_catalogs(
            catalogs, harvest='none')

        for catalog in harvest_none:
            # Una lista vacía es "falsa"
            assert_false(catalog["dataset"])

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

        assert_list_equal(actual, expected)

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
        assert_list_equal(actual, expected)

    def test_generate_datasets_summary(self):
        """Genera informe conciso sobre datasets correctamente."""
        catalog = os.path.join(self.SAMPLES_DIR,
                               "several_datasets_for_harvest.json")
        actual = self.dj.generate_datasets_summary(catalog)
        expected = [
            OrderedDict([('indice', 0),
                         ('titulo',
                          'Sistema de contrataciones electrónicas UNO'),
                         ('identificador', '1'),
                         ('estado_metadatos', 'ERROR'),
                         ('cant_errores', 4),
                         ('cant_distribuciones', 4)]),
            OrderedDict([('indice', 1),
                         ('titulo',
                          'Sistema de contrataciones electrónicas DOS'),
                         ('identificador', '2'),
                         ('estado_metadatos', 'OK'),
                         ('cant_errores', 0),
                         ('cant_distribuciones', 1)]),
            OrderedDict([('indice', 2),
                         ('titulo',
                          'Sistema de contrataciones electrónicas TRES'),
                         ('identificador', '3'),
                         ('estado_metadatos', 'OK'),
                         ('cant_errores', 0),
                         ('cant_distribuciones', 1)])]

        assert_list_equal(actual, expected)

    def test_DataJson_constructor(self):
        for key, value in iteritems(self.catalog):
            if key != "dataset":
                assert_equal(self.dj[key], value)

    def test_datasets_property(self):
        """La propiedad datasets equivale a clave 'dataset' de un catalog."""
        assert_equal(self.dj.datasets,
                     pydatajson.DataJson(self.catalog)["dataset"])
        assert_equal(self.dj.datasets, self.dj["dataset"])

    @load_expected_result()
    def test_datasets(self, expected_result):
        datasets = self.dj.get_datasets()
        pprint(datasets)
        assert_equal(expected_result, datasets)

        datasets = self.dj.datasets
        pprint(datasets)
        assert_equal(expected_result, datasets)

    def test_datasets_without_catalog(self):
        with assert_raises(KeyError):
            dj = pydatajson.DataJson()
            datasets = dj.get_datasets()

        with assert_raises(KeyError):
            dj = pydatajson.DataJson()
            datasets = dj.datasets

    def test_distributions_property(self):
        """La propiedad distributions equivale
        a clave 'distribution' de un catalog."""
        assert_equal(self.dj.distributions,
                     pydatajson.DataJson(self.catalog).get_distributions())

    @load_expected_result()
    def test_distributions(self, expected_result):
        distributions = self.dj.get_distributions()
        pprint(distributions)
        assert_equal(expected_result, distributions)

        distributions = self.dj.distributions
        pprint(distributions)
        assert_equal(expected_result, distributions)

    def test_distributions_without_catalog(self):
        with assert_raises(KeyError):
            dj = pydatajson.DataJson()
            distributions = dj.get_distributions()

        with assert_raises(KeyError):
            dj = pydatajson.DataJson()
            distributions = dj.distributions

    def test_fields_property(self):
        """La propiedad fields equivale a clave 'field' de un catalog."""
        fields = []
        for dataset in self.catalog["dataset"]:
            for distribution in dataset["distribution"]:
                if "field" in distribution:
                    for field in distribution["field"]:
                        field["dataset_identifier"] = dataset["identifier"]
                        field["distribution_identifier"] = distribution[
                            "identifier"]
                        fields.append(field)
        assert_equal(self.dj.fields, fields)

        fields = []
        for dataset in self.dj["dataset"]:
            for distribution in dataset["distribution"]:
                if "field" in distribution:
                    for field in distribution["field"]:
                        field["dataset_identifier"] = dataset["identifier"]
                        field["distribution_identifier"] = distribution[
                            "identifier"]
                        fields.append(field)
        assert_equal(self.dj.fields, fields)

    @load_expected_result()
    def test_fields(self, expected_result):
        fields = self.dj.get_fields()
        pprint(fields)
        assert_equal(expected_result, fields)

        fields = self.dj.fields
        pprint(fields)
        assert_equal(expected_result, fields)

    def test_fields_without_catalog(self):
        with assert_raises(KeyError):
            dj = pydatajson.DataJson()
            fields = dj.get_fields()

        with assert_raises(KeyError):
            dj = pydatajson.DataJson()
            fields = dj.fields


if __name__ == '__main__':
    nose.run(defaultTest=__name__)
