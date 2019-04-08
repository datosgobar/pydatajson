# -*- coding: utf-8 -*-

"""Tests del modulo catalog_readme."""

from __future__ import print_function, unicode_literals, with_statement

import io
import os.path

import vcr
from nose.tools import assert_true, assert_equal

try:
    import mock
except ImportError:
    from unittest import mock
import filecmp

from pydatajson.catalog_readme import generate_readme
from tests.support.decorators import RESULTS_DIR

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
        cls.catalog = cls.get_sample("several_datasets_for_harvest.json")

    @my_vcr.use_cassette()
    def test_generate_readme(self):
        with io.open(os.path.join(self.RESULTS_DIR, "catalog_readme.md"), 'r',
                     encoding='utf-8') as expected_readme_file:
            expected_readme = expected_readme_file.read()
            readme = generate_readme(self.catalog)
            assert_equal(expected_readme, readme)

    @my_vcr.use_cassette()
    def test_readme_file_write(self):
        actual_filename = os.path.join(self.TEMP_DIR, "catalog_readme.md")
        expected_filename = os.path.join(self.RESULTS_DIR, "catalog_readme.md")
        generate_readme(self.catalog, export_path=actual_filename)
        comparison = filecmp.cmp(actual_filename, expected_filename)
        if comparison:
            os.remove(actual_filename)
        else:
            """
{} se escribió correctamente, pero no es idéntico al esperado. Por favor,
revíselo manualmente""".format(actual_filename)

        assert_true(comparison)

    @my_vcr.use_cassette()
    @mock.patch('pydatajson.indicators._federation_indicators')
    def test_readme_null_indicators(self, mock_indicators):
        mock_indicators.return_value = {
            'datasets_federados_cant': None,
            'datasets_federados_pct': None,
            'datasets_no_federados_cant': None,
            'datasets_federados_eliminados_cant': None,
            'distribuciones_federadas_cant': None,
            'datasets_federados_eliminados': [],
            'datasets_no_federados': [],
            'datasets_federados': [],
            }
        results_path = os.path.join(
            self.RESULTS_DIR, "null_indicators_readme.md")

        with io.open(results_path, 'r', encoding='utf-8') \
                as expected_readme_file:
            expected_readme = expected_readme_file.read()
            readme = generate_readme(self.catalog)
            assert_equal(expected_readme, readme)
