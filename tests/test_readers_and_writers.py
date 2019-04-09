#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests del modulo pydatajson."""

from __future__ import print_function, unicode_literals, with_statement

import os.path
import unittest
import nose
import vcr

from tempfile import NamedTemporaryFile

from tests.support.factories.xlsx import CSV_TABLE, WRITE_XLSX_TABLE
from tests.support.factories.xlsx import READ_XLSX_TABLE

try:
    import mock
except ImportError:
    from unittest import mock
import filecmp
from tests.context import pydatajson
from pydatajson.core import DataJson
from pydatajson.helpers import ensure_dir_exists
from pydatajson.custom_exceptions import NonParseableCatalog
from tests import xl_methods
import openpyxl as pyxl

my_vcr = vcr.VCR(path_transformer=vcr.VCR.ensure_suffix('.yaml'),
                 cassette_library_dir=os.path.join(
                     "tests", "cassetes", "readers_and_writers"),
                 record_mode='once')


class ReadersAndWritersTestCase(unittest.TestCase):
    SAMPLES_DIR = os.path.join("tests", "samples")
    RESULTS_DIR = os.path.join("tests", "results")
    TEMP_DIR = os.path.join("tests", "temp")

    @classmethod
    def get_sample(cls, sample_filename):
        return os.path.join(cls.SAMPLES_DIR, sample_filename)

    @classmethod
    def setUp(cls):
        ensure_dir_exists(cls.SAMPLES_DIR)
        ensure_dir_exists(cls.RESULTS_DIR)
        ensure_dir_exists(cls.TEMP_DIR)
        cls.dj = DataJson()
        cls.maxDiff = None
        cls.longMessage = True

    @classmethod
    def tearDown(cls):
        del (cls.dj)

    # TESTS DE READ_TABLE y WRITE_TABLE

    def test_read_table_from_csv(self):
        csv_filename = os.path.join(self.SAMPLES_DIR, "read_table.csv")
        actual_table = pydatajson.readers.read_table(csv_filename)
        expected_table = CSV_TABLE

        for (actual_row, expected_row) in zip(actual_table, expected_table):
            self.assertEqual(actual_row, expected_row)

    def test_read_table_from_xlsx(self):
        xlsx_filename = os.path.join(self.SAMPLES_DIR, "read_table.xlsx")
        actual_table = pydatajson.readers.read_table(xlsx_filename)
        expected_table = READ_XLSX_TABLE

        for (actual_row, expected_row) in zip(actual_table, expected_table):
            self.assertEqual(dict(actual_row), dict(expected_row))

        self.assertListEqual(actual_table, expected_table)

    @nose.tools.raises(ValueError)
    def test_read_table_from_invalid_format(self):
        """Si se quiere leer un formato desconocido (no XLSX ni CSV),
        read_table levanta un Assertion Error."""
        pydatajson.readers.read_table(
            os.path.join(self.SAMPLES_DIR, "full_data.json"))

    def test_write_table_to_csv(self):
        expected_filename = os.path.join(self.RESULTS_DIR, "write_table.csv")
        actual_filename = os.path.join(self.TEMP_DIR, "write_table.csv")

        pydatajson.writers.write_table(CSV_TABLE, actual_filename)
        comparison = filecmp.cmp(actual_filename, expected_filename)
        if comparison:
            os.remove(actual_filename)
        else:
            """
{} se escribió correctamente, pero no es idéntico al esperado. Por favor,
revíselo manualmente""".format(actual_filename)

        self.assertTrue(comparison)

    def test_write_table_to_xlsx(self):
        expected_filename = os.path.join(self.RESULTS_DIR, "write_table.xlsx")
        actual_filename = os.path.join(self.TEMP_DIR, "write_table.xlsx")

        pydatajson.writers.write_table(WRITE_XLSX_TABLE, actual_filename)
        expected_wb = pyxl.load_workbook(expected_filename)
        actual_wb = pyxl.load_workbook(actual_filename)

        self.assertTrue(xl_methods.compare_cells(actual_wb, expected_wb))

        os.remove(actual_filename)

    @nose.tools.raises(ValueError)
    def test_write_table_to_invalid_format(self):
        """Si se quiere escribir un formato desconocido (no XLSX ni CSV),
        write_table levanta un Assertion Error."""
        pydatajson.writers.write_table(
            CSV_TABLE, os.path.join(self.SAMPLES_DIR, "full_data.json"))

    def test_write_read_csv_loop(self):
        """Escribir y leer un CSV es una operacion idempotente."""
        temp_filename = os.path.join(self.TEMP_DIR, "write_read_loop.csv")
        pydatajson.writers.write_table(CSV_TABLE, temp_filename)
        read_table = pydatajson.readers.read_table(temp_filename)

        comparison = (CSV_TABLE == read_table)
        if comparison:
            os.remove(temp_filename)
        else:
            """
{} se escribió correctamente, pero no es idéntico al esperado. Por favor,
revíselo manualmente""".format(temp_filename)

        self.assertListEqual(read_table, CSV_TABLE)

    def test_write_read_xlsx_loop(self):
        """Escribir y leer un XLSX es una operacion idempotente."""
        temp_filename = os.path.join(self.TEMP_DIR, "write_read_loop.xlsx")
        pydatajson.writers.write_table(WRITE_XLSX_TABLE, temp_filename)
        read_table = pydatajson.readers.read_table(temp_filename)

        # read_xlsx_table no lee celdasd nulas. Por lo tanto, si hay una clave
        # de valor None en la tabla original, al leerla y escribirla dicha
        # clave no estará presente. Por eso se usa d.get(k) en lugar de d[k].
        for (actual_row, expected_row) in zip(read_table, WRITE_XLSX_TABLE):
            for key in expected_row.keys():
                self.assertEqual(actual_row.get(key), expected_row.get(key))

        os.remove(temp_filename)

    # TESTS DE READ_CATALOG

    def test_read_catalog_passes_dictionaries(self):
        """read_catalog "no toca" el input si recibe un diccionario."""
        a_dict = {"a": 1, "b": 2}
        self.assertEqual(a_dict, pydatajson.readers.read_catalog(a_dict))

    def test_read_local_xlsx_catalog(self):
        """read_catalog puede leer XLSX locales."""
        expected_catalog = pydatajson.readers.read_catalog(
            os.path.join(self.SAMPLES_DIR, "catalogo_justicia.json"))
        actual_catalog = pydatajson.readers.read_catalog(
            os.path.join(self.SAMPLES_DIR, "catalogo_justicia.xlsx"))

        self.assertDictEqual(actual_catalog, expected_catalog)

    def test_read_written_xlsx_catalog(self):
        """read_catalog puede leer XLSX creado por write_xlsx_catalog"""
        original_catalog = DataJson(
            os.path.join(self.SAMPLES_DIR, "catalogo_justicia.json"))

        tmp_xlsx = os.path.join(self.TEMP_DIR, "xlsx_catalog.xlsx")
        pydatajson.writers.write_xlsx_catalog(original_catalog, tmp_xlsx)

        try:
            pydatajson.readers.read_xlsx_catalog(tmp_xlsx)
        except NonParseableCatalog:
            self.fail("No se pudo leer archivo XLSX")

    def test_read_local_xlsx_catalog_with_defaults(self):
        """read_catalog puede leer con valores default."""
        expected_catalog = pydatajson.readers.read_catalog(
            os.path.join(self.SAMPLES_DIR,
                         "catalogo_justicia_with_defaults.json"))
        actual_catalog = pydatajson.readers.read_catalog(
            os.path.join(self.SAMPLES_DIR,
                         "catalogo_justicia_with_defaults.xlsx"),
            default_values={
                "dataset_issued": "2017-06-22",
                "distribution_issued": "2017-06-22",
                "catalog_publisher_mbox": "a@b.com",
                "field_description": "Una descripcion default"
            }
        )

        self.assertDictEqual(actual_catalog, expected_catalog)

    def test_read_local_xlsx_catalog_extra_columns(self):
        """read_catalog ignora las columnas extras."""
        expected_catalog = pydatajson.readers.read_catalog(
            os.path.join(self.SAMPLES_DIR,
                         "catalogo_justicia.json"))
        actual_catalog = pydatajson.readers.read_catalog(
            os.path.join(self.SAMPLES_DIR,
                         "catalogo_justicia_extra_columns.xlsx"))

        self.assertDictEqual(actual_catalog, expected_catalog)

    @my_vcr.use_cassette()
    def test_read_remote_xlsx_catalog(self):
        """read_catalog puede leer XLSX remotos."""
        catalog_url = "".join([
            "https://github.com/datosgobar/pydatajson/raw/master/",
            "tests/samples/catalogo_justicia.xlsx"])

        expected_catalog = pydatajson.readers.read_catalog(
            os.path.join(self.SAMPLES_DIR, "catalogo_justicia.json"))
        actual_catalog = pydatajson.readers.read_catalog(catalog_url)

        self.assertDictEqual(actual_catalog, expected_catalog)

    @mock.patch('pydatajson.writers.write_json')
    def test_write_json_catalog_is_write_json(self, mock_write_json):
        obj = [1, 2, 3]
        path = os.path.join(self.TEMP_DIR, "test.json")

        pydatajson.writers.write_json_catalog(obj, path)

        pydatajson.writers.write_json.assert_called_once_with(obj, path)

    def test_read_write_both_formats_yields_the_same(self):
        for suffix in ['xlsx', 'json']:
            catalog = DataJson(os.path.join(self.SAMPLES_DIR,
                                            "catalogo_justicia." + suffix))
            catalog.to_json(os.path.join(self.TEMP_DIR,
                                         "saved_catalog.json"))
            catalog.to_xlsx(os.path.join(self.TEMP_DIR,
                                         "saved_catalog.xlsx"))
            catalog_json = DataJson(os.path.join(self.TEMP_DIR,
                                                 "saved_catalog.xlsx"))
            catalog_xlsx = DataJson(os.path.join(self.TEMP_DIR,
                                                 "saved_catalog.xlsx"))
            self.assertEqual(catalog_json, catalog_xlsx)

            # la llamada to_xlsx() genera los indices en el catalogo original
            # aplicarla a los catalogos generados debería dejarlos igual al
            # original
            catalog_xlsx.to_xlsx(os.path.join(self.TEMP_DIR,
                                              "otro.xlsx"))
            catalog_json.to_xlsx(os.path.join(self.TEMP_DIR,
                                              "otro.xlsx"))

            self.assertEqual(catalog_json, catalog)
            self.assertEqual(catalog_xlsx, catalog)

    def test_read_xlsx_lists_with_extra_commas(self):
        # No hay valores vacíos a pesar que hay listas con comas extras
        catalog = pydatajson.readers.read_catalog(
            self.get_sample("lists_extra_commas.xlsx"))
        self.assertTrue(catalog['language'])
        self.assertTrue(all(catalog['language']))
        for dataset in catalog['dataset']:
            for field in ['theme', 'superTheme', 'keyword']:
                # Listas no vacias
                self.assertTrue(dataset[field])
                # Elementos no vacios
                self.assertTrue(all(dataset[field]))

    def test_read_suffixless_json(self):
        original = pydatajson.readers.read_catalog(
            self.get_sample('full_data.json'))
        suffixless = pydatajson.readers.read_catalog(
            self.get_sample('full_data_no_json_suffix'))
        self.assertDictEqual(original, suffixless)

    def test_read_suffixless_xlsx(self):
        original = pydatajson.readers.read_catalog(
            self.get_sample('catalogo_justicia.xlsx'))
        suffixless = pydatajson.readers.read_catalog(
            self.get_sample('catalogo_justicia_no_xlsx_suffix'))
        self.assertDictEqual(original, suffixless)

    @mock.patch('pydatajson.readers.read_json', return_value='test_catalog')
    def test_force_json_format(self, mock_reader):
        catalog = pydatajson.readers.read_catalog('full_data.xlsx',
                                                  catalog_format='json')
        self.assertEqual('test_catalog', catalog)

    @mock.patch('pydatajson.readers.read_xlsx_catalog',
                return_value='test_catalog')
    def test_force_xlsx_format(self, mock_reader):
        catalog = pydatajson.readers.read_catalog('full_data.json',
                                                  catalog_format='xlsx')
        self.assertEqual('test_catalog', catalog)

    @mock.patch('pydatajson.readers.read_ckan_catalog',
                return_value='test_catalog')
    def test_force_ckan_format(self, mock_reader):
        catalog = pydatajson.readers.read_catalog('full_data',
                                                  catalog_format='ckan')
        self.assertEqual('test_catalog', catalog)

    @nose.tools.raises(NonParseableCatalog)
    def test_read_failing_json_catalog_raises_non_parseable_error(self):
        pydatajson.readers.read_catalog('inexistent_file.json')

    @nose.tools.raises(NonParseableCatalog)
    def test_read_failing_xlsx_catalog_raises_non_parseable_error(self):
        pydatajson.readers.read_catalog('inexistent_file.xlsx')

    @nose.tools.raises(NonParseableCatalog)
    def test_failing_suffixless_catalog_raises_non_parseable_error(self):
        pydatajson.readers.read_catalog('inexistent_file')

    def test_xlsx_write_missing_optional_fields_and_themes(self):
        with NamedTemporaryFile(suffix='.xlsx') as tempfile:
            catalog = DataJson(os.path.join(self.SAMPLES_DIR,
                                            "minimum_data.json"))
            catalog.to_xlsx(tempfile.name)
            written_datajson = DataJson(tempfile.name)
        written_dataset = written_datajson.datasets[0]
        written_distribution = written_datajson.distributions[0]
        self.assertTrue('theme' not in written_dataset)
        self.assertTrue('field' not in written_distribution)


if __name__ == '__main__':
    nose.run(defaultTest=__name__)
