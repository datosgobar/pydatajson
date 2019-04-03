# -*- coding: utf-8 -*-

"""Tests del modulo pydatajson."""

from __future__ import print_function, unicode_literals, with_statement

import os.path

import vcr
from nose.tools import assert_true, assert_false, assert_equal

try:
    import mock
except ImportError:
    from unittest import mock

from pydatajson.core import DataJson
from pydatajson import readers
from .support.decorators import RESULTS_DIR

my_vcr = vcr.VCR(
    path_transformer=vcr.VCR.ensure_suffix('.yaml'),
    cassette_library_dir=os.path.join(
        "tests",
        "cassetes",
        "indicators"),
    record_mode='once')


class TestIndicatorsTestCase(object):
    SAMPLES_DIR = os.path.join("tests", "samples")
    RESULTS_DIR = RESULTS_DIR
    TEMP_DIR = os.path.join("tests", "temp")

    @classmethod
    def get_sample(cls, sample_filename):
        return os.path.join(cls.SAMPLES_DIR, sample_filename)

    @classmethod
    def setUp(cls):
        cls.dj = DataJson(cls.get_sample("full_data.json"))
        cls.catalog = readers.read_catalog(
            cls.get_sample("full_data.json"))
        cls.maxDiff = None
        cls.longMessage = True

    @classmethod
    def tearDown(cls):
        del (cls.dj)

    @my_vcr.use_cassette()
    def test_generate_catalog_indicators(self):
        catalog = os.path.join(self.SAMPLES_DIR, "several_datasets.json")

        indicators = self.dj.generate_catalogs_indicators(catalog)[0][0]

        # Resultados esperados haciendo cuentas manuales sobre el catálogo
        expected = {
            'identifier': '7d4d816f-3a40-476e-ab71-d48a3f0eb3c8',
            'title': 'Cosechando Datos Argentina',
            'datasets_cant': 3,
            'distribuciones_cant': 6,
            'datasets_meta_ok_cant': 2,
            'datasets_meta_error_cant': 1,
            'datasets_meta_ok_pct': 0.6667,
            'datasets_con_datos_cant': 2,
            'datasets_sin_datos_cant': 1,
            'datasets_con_datos_pct': 0.6667,
        }

        for k, v in expected.items():
            assert_equal(indicators[k], v)

    @my_vcr.use_cassette()
    def test_date_indicators(self):
        from datetime import datetime
        catalog = os.path.join(self.SAMPLES_DIR, "several_datasets.json")

        indicators = self.dj.generate_catalogs_indicators(catalog)[0][0]
        dias_diff = (datetime.now() - datetime(2016, 4, 14)).days

        expected = {
            'catalogo_ultima_actualizacion_dias': dias_diff,
            'datasets_actualizados_cant': 1,
            'datasets_desactualizados_cant': 2,
            'datasets_actualizados_pct': 0.3333,
            'datasets_frecuencia_cant': {
                'R/P1W': 1,
                'R/P1M': 1,
                'eventual': 1
            },
        }

        for k, v in expected.items():
            assert_equal(indicators[k], v)

    @my_vcr.use_cassette()
    def test_format_indicators(self):
        catalog = os.path.join(self.SAMPLES_DIR, "several_datasets.json")

        indicators = self.dj.generate_catalogs_indicators(catalog)[0][0]

        expected = {
            'distribuciones_formatos_cant': {
                'CSV': 1,
                'XLSX': 1,
                'PDF': 1,
                'None': 3
            }
        }

        for k, v in expected.items():
            assert_equal(indicators[k], v)

    @my_vcr.use_cassette()
    def test_license_indicators(self):
        catalog = os.path.join(
            self.SAMPLES_DIR,
            "several_datasets_with_licenses.json")

        indicators = self.dj.generate_catalogs_indicators(catalog)[0][0]

        expected = {
            'datasets_licencias_cant': {
                'Open Data Commons Open Database License 1.0': 1,
                'Creative Commons Attribution': 1,
                'None': 1
            }
        }

        for k, v in expected.items():
            assert_equal(indicators[k], v)

    @my_vcr.use_cassette()
    def test_no_licenses_indicators(self):
        # No tienen licencias
        catalog = os.path.join(
            self.SAMPLES_DIR,
            "several_datasets_for_harvest.json")
        indicators = self.dj.generate_catalogs_indicators(catalog)[0][0]
        assert_equal(indicators['datasets_licencias_cant'], {'None': 3})

    @my_vcr.use_cassette()
    def test_field_indicators_on_min_catalog(self):
        catalog = os.path.join(self.SAMPLES_DIR, "minimum_data.json")

        # Se espera un único catálogo como resultado, índice 0
        indicators = self.dj.generate_catalogs_indicators(catalog)[0][0]

        expected = {
            'campos_recomendados_pct': 0.0,
            'campos_optativos_pct': 0.0,
        }

        for k, v in expected.items():
            assert_equal(indicators[k], v)

    @my_vcr.use_cassette()
    def test_field_indicators_on_full_catalog(self):
        catalog = os.path.join(self.SAMPLES_DIR, "full_data.json")

        # Se espera un único catálogo como resultado, índice 0
        indicators = self.dj.generate_catalogs_indicators(catalog)[0][0]

        expected = {
            'campos_recomendados_pct': 0.9545,
            'campos_optativos_pct': 1.0000
        }

        for k, v in expected.items():
            assert_equal(indicators[k], v)

    @my_vcr.use_cassette()
    def test_federation_indicators_same_catalog(self):
        catalog = os.path.join(self.SAMPLES_DIR, "several_datasets.json")

        indicators = self.dj.generate_catalogs_indicators(catalog, catalog)[1]

        # Esperado: todos los datasets están federados
        expected = {
            'datasets_federados_cant': 3,
            'datasets_no_federados_cant': 0,
            'datasets_no_federados': [],
            'datasets_federados_pct': 1.0000,
            'distribuciones_federadas_cant': 6
        }

        for k, v in expected.items():
            assert_equal(indicators[k], v)

    @my_vcr.use_cassette()
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
            'datasets_federados_pct': 0.00,
            'distribuciones_federadas_cant': 0
        }

        for k, v in expected.items():
            assert_equal(indicators[k], v)

    @my_vcr.use_cassette()
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
            assert_equal(indicators[k], v)

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
            "datasets_federados_eliminados": [
                ('Base de datos legislativos Infoleg',
                 "http://datos.jus.gob.ar/dataset/base-de-datos"
                 "-legislativos-infoleg")]}

        for k, v in expected.items():
            assert_equal(indicators[k], v)

    @my_vcr.use_cassette()
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
            'datasets_cant': 5,
            'distribuciones_cant': 8,
            'datasets_meta_ok_cant': 4,
            'datasets_meta_error_cant': 1,
            'datasets_meta_ok_pct': 0.8000,
            'datasets_con_datos_cant': 3,
            'datasets_sin_datos_cant': 2,
            'datasets_con_datos_pct': 0.6000,
            'distribuciones_formatos_cant': {
                'CSV': 2,
                'XLSX': 1,
                'PDF': 2,
                'None': 3
            },
            'distribuciones_tipos_cant': {
                'file': 1,
                'documentation': 1,
                'None': 6
            },
            'datasets_licencias_cant': {
                'Open Data Commons Open Database License 1.0': 2,
                'None': 3
            },
            'campos_optativos_pct': 0.3256,
            'campos_recomendados_pct': 0.5072,
        }

        for k, v in expected.items():
            assert_equal(network_indicators[k], v)

    @my_vcr.use_cassette()
    def test_network_license_indicators(self):
        one_catalog = os.path.join(
            self.SAMPLES_DIR,
            "several_datasets_with_licenses.json")
        other_catalog = os.path.join(self.SAMPLES_DIR, "full_data.json")

        indicators, network_indicators = self.dj.generate_catalogs_indicators([
            one_catalog,
            other_catalog
        ])
        # Esperado: 2 ODbL en full, 1 en several
        # 1 Creative Commons en several
        # 1 Dataset en several sin licencias
        expected = {
            'catalogos_cant': 2,
            'datasets_cant': 5,
            'datasets_licencias_cant': {
                'Open Data Commons Open Database License 1.0': 3,
                'Creative Commons Attribution': 1,
                'None': 1
            },
        }

        for k, v in expected.items():
            assert_equal(network_indicators[k], v)

    @my_vcr.use_cassette()
    def test_network_type_indicators(self):
        one_catalog = os.path.join(
            self.SAMPLES_DIR,
            "several_datasets_with_types.json")
        other_catalog = os.path.join(self.SAMPLES_DIR, "full_data.json")

        indicators, network_indicators = self.dj.generate_catalogs_indicators([
            one_catalog,
            other_catalog
        ])
        # Esperado: 1 file en full, 1 en several
        # 1 file.upload en several
        # 1 documentation en full, 1 en several
        # 2 api en several
        # 1 distribucion en several sin tipo
        expected = {
            'catalogos_cant': 2,
            'distribuciones_cant': 8,
            'distribuciones_tipos_cant': {
                'file': 2,
                'file.upload': 1,
                'documentation': 2,
                'api': 2,
                'None': 1,
            }
        }

        for k, v in expected.items():
            assert_equal(network_indicators[k], v, k)

    @my_vcr.use_cassette()
    def test_types_indicators(self):
        catalog = os.path.join(
            self.SAMPLES_DIR,
            "several_datasets_with_types.json")

        indicators = self.dj.generate_catalogs_indicators(catalog)[0][0]

        expected = {
            'distribuciones_tipos_cant': {
                'file': 1,
                'file.upload': 1,
                'documentation': 1,
                'api': 2,
                'None': 1
            }
        }

        for k, v in expected.items():
            assert_equal(indicators[k], v)

    def test_network_federation_indicators(self):
        one_catalog = os.path.join(self.SAMPLES_DIR, "several_datasets.json")
        other_catalog = os.path.join(self.SAMPLES_DIR, "full_data.json")
        central = one_catalog
        indicators, network_indicators = self.dj.generate_catalogs_indicators([
            one_catalog,
            other_catalog
        ], central)

        # Esperado: Los datasets de several estan federados y los de full, no
        expected = {
            'datasets_federados_cant': 3,
            'datasets_no_federados_cant': 2,
            'datasets_federados_pct': 0.6000,
            'distribuciones_federadas_cant': 6
        }
        for k, v in expected.items():
            assert_equal(network_indicators[k], v)

    @my_vcr.use_cassette()
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
            assert_equal(indicators[k], v, k)

    @my_vcr.use_cassette()
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
            assert_equal(indicators[k], v, k)

    @my_vcr.use_cassette()
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
            'datasets_licencias_cant': {},
            'datasets_frecuencia_cant': {}
        }

        for k, v in expected.items():
            assert_equal(indicators[k], v, k)

    @my_vcr.use_cassette()
    def test_last_updated_indicator_missing_issued_field(self):
        from datetime import datetime
        catalog = os.path.join(self.SAMPLES_DIR, "minimum_data.json")

        indicators = self.dj.generate_catalogs_indicators(catalog)[0][0]
        dias_diff = (datetime.now() - datetime(2016, 4, 14)).days

        # Catálogo no tiene 'issued', pero su dataset sí -> uso el del dataset
        expected = {
            'catalogo_ultima_actualizacion_dias': dias_diff
        }

        for k, v in expected.items():
            assert_equal(indicators[k], v, k)

    def test_dataset_is_updated(self):
        catalog = os.path.join(self.SAMPLES_DIR, "catalogo_justicia.json")

        # Datasset con periodicity mensual vencida
        dataset = "Base de datos legislativos Infoleg"
        assert_false(self.dj.dataset_is_updated(catalog, dataset))

        # Dataset con periodicity eventual, siempre True
        dataset = "Declaración Jurada Patrimonial Integral de carácter público"
        assert_true(self.dj.dataset_is_updated(catalog, dataset))

    @my_vcr.use_cassette()
    def test_date_network_indicators_empty_catalog(self):
        catalog = os.path.join(self.SAMPLES_DIR, "invalid_catalog_empty.json")
        indics, network_indics = self.dj.generate_catalogs_indicators(
            [catalog,
             catalog]
        )

        for k, v in network_indics.items():
            assert_true(v is not None)

    def test_unreachable_catalogs(self):
        catalog = os.path.join(self.SAMPLES_DIR, "invalid/path.json")
        indics, network_indics = self.dj.generate_catalogs_indicators(
            [catalog,
             catalog]
        )
        assert_equal([], indics)
        assert_equal({}, network_indics)

    @my_vcr.use_cassette()
    def test_valid_and_unreachable_catalogs(self):
        valid = os.path.join(self.SAMPLES_DIR, "several_datasets.json")
        unreachable = os.path.join(self.SAMPLES_DIR, "invalid/path.json")

        indicators = self.dj.generate_catalogs_indicators(
            [valid, unreachable])[0][0]

        # El resultado ignora el catálogo inaccesible
        expected = {
            'datasets_cant': 3,
            'distribuciones_cant': 6,
            'datasets_meta_ok_cant': 2,
            'datasets_meta_error_cant': 1,
            'datasets_meta_ok_pct': 0.6667,
        }

        for k, v in expected.items():
            assert_true(indicators[k], v)

    def test_unreachable_central_catalog(self):
        catalog = os.path.join(self.SAMPLES_DIR, "several_datasets.json")
        unreachable = os.path.join(self.SAMPLES_DIR, "invalid/path.json")
        indics = self.dj.generate_catalogs_indicators(
            catalog, central_catalog=unreachable)[0][0]
        expected = {
            'datasets_cant': 3,
            'distribuciones_cant': 6,
            'datasets_meta_ok_cant': 2,
            'datasets_meta_error_cant': 1,
            'datasets_meta_ok_pct': 0.6667,
            'datasets_federados_cant': None,
            'datasets_no_federados_cant': None,
            'datasets_federados_pct': None,
            'datasets_federados': [],
            'datasets_no_federados': [],
            'datasets_federados_eliminados': [],

        }
        for k, v in expected.items():
            assert_equal(indics[k], v)

    @my_vcr.use_cassette()
    @mock.patch(
        'pydatajson.indicators.generate_datasets_summary',
        autospec=True)
    def test_bad_summary(self, mock_summary):
        mock_summary.side_effect = Exception('bad summary')
        catalog = os.path.join(self.SAMPLES_DIR, "several_datasets.json")
        indics = self.dj.generate_catalogs_indicators(catalog)[0][0]
        expected = {
            'datasets_cant': None,
            'distribuciones_cant': None,
            'datasets_meta_ok_cant': None,
            'datasets_meta_error_cant': None,
            'datasets_meta_ok_pct': None
        }
        for k, v in expected.items():
            assert_equal(indics[k], v)

    @my_vcr.use_cassette()
    def test_bad_date_indicators(self):
        catalog = self.dj
        catalog['issued'] = catalog['modified'] = 'invalid_date'
        indics = self.dj.generate_catalogs_indicators()[0][0]
        expected = {
            'datasets_desactualizados_cant': None,
            'datasets_actualizados_cant': None,
            'datasets_actualizados_pct': None,
            'catalogo_ultima_actualizacion_dias': None,
            'datasets_frecuencia_cant': {}
        }
        for k, v in expected.items():
            assert_equal(indics[k], v)

    @my_vcr.use_cassette()
    def test_no_title_nor_identifier_catalog(self):
        catalog = DataJson(
            os.path.join(
                self.SAMPLES_DIR,
                "missing_catalog_title.json"))
        del catalog['identifier']
        indics = self.dj.generate_catalogs_indicators(catalog)[0][0]
        assert_equal(indics['title'], 'no-title')
        assert_equal(indics['identifier'], 'no-id')

    def test_node_indicators_no_central_catalog(self):
        catalog = os.path.join(self.SAMPLES_DIR, "several_datasets.json")
        node_indicators, network_indicators = \
            self.dj.generate_catalogs_indicators(catalog)

        # Esperado: no se calculan indicadores de federación
        federation_indicators = [
            'datasets_federados_cant',
            'datasets_no_federados_cant',
            'datasets_no_federados',
            'distribuciones_federadas_cant']

        for fed_ind in federation_indicators:
            assert_true(fed_ind not in node_indicators[0])
            assert_true(fed_ind not in network_indicators)

    def test_federation_indicators_by_id(self):
        catalogs = [
            os.path.join(self.SAMPLES_DIR, "federated_1.json"),
            os.path.join(self.SAMPLES_DIR, "federated_2.json"),
        ]
        central = os.path.join(self.SAMPLES_DIR, "central.json")
        indicators = self.dj.generate_catalogs_indicators(
            catalogs, central, identifier_search=True)[1]

        expected = {
            'datasets_federados_cant': 2,
            'datasets_no_federados_cant': 2,
            'datasets_no_federados': [
                ('Sistema de contrataciones electrónicas',
                 'http://datos.gob.ar/dataset/contrataciones-electronicas'),
                ('Sistema de contrataciones electrónicas (sin datos)',
                 'http://datos.gob.ar/dataset/argentina-compra'),
            ],
            'datasets_federados_pct': 0.5000,
            'distribuciones_federadas_cant': 2
        }

        for k, v in expected.items():
            assert_equal(indicators[k], v)
