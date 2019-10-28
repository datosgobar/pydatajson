# -*- coding: utf-8 -*-

import os.path
import re
import unittest

import requests_mock

from pydatajson.status_indicators_generator import StatusIndicatorsGenerator

try:
    import mock
except ImportError:
    from unittest import mock


class TestStatusIndicatorsGeneratorTestCase(unittest.TestCase):
    SAMPLES_DIR = os.path.join("tests", "samples")

    @classmethod
    def get_sample(cls, sample_filename):
        return os.path.join(cls.SAMPLES_DIR, sample_filename)

    @classmethod
    def setUpClass(cls):
        with mock.patch(
                'pydatajson.validators'
                '.url_validator.UrlValidator.is_working_url',
                return_value=(True, 200)):
            cls.gen_justicia = StatusIndicatorsGenerator(
                cls.get_sample('catalogo_justicia.json'))
            cls.gen_full_data = StatusIndicatorsGenerator(
                cls.get_sample('full_data.json'))
            cls.gen_empty = StatusIndicatorsGenerator(
                cls.get_sample('invalid_catalog_empty.json'))

    def test_just_datasets_cant(self):
        self.assertEqual(16, self.gen_justicia.datasets_cant())

    def test_full_datasets_cant(self):
        self.assertEqual(2, self.gen_full_data.datasets_cant())

    def test_empty_datasets_cant(self):
        self.assertEqual(0, self.gen_empty.datasets_cant())

    def test_just_distribuciones_cant(self):
        self.assertEqual(56, self.gen_justicia.distribuciones_cant())

    def test_full_distribuciones_cant(self):
        self.assertEqual(2, self.gen_full_data.distribuciones_cant())

    def test_empty_distribuciones_cant(self):
        self.assertEqual(0, self.gen_empty.distribuciones_cant())

    def test_just_datasets_meta_ok_cant(self):
        self.assertEqual(15, self.gen_justicia.datasets_meta_ok_cant())

    def test_full_datasets_meta_ok_cant(self):
        self.assertEqual(2, self.gen_full_data.datasets_meta_ok_cant())

    def test_empty_datasets_meta_ok_cant(self):
        self.assertEqual(0, self.gen_empty.datasets_meta_ok_cant())

    def test_just_datasets_meta_error_cant(self):
        self.assertEqual(1, self.gen_justicia.datasets_meta_error_cant())

    def test_full_datasets_meta_error_cant(self):
        self.assertEqual(0, self.gen_full_data.datasets_meta_error_cant())

    def test_empty_datasets_meta_error_cant(self):
        self.assertEqual(0, self.gen_empty.datasets_meta_error_cant())

    def test_just_datasets_meta_ok_pct(self):
        self.assertEqual(0.9375, self.gen_justicia.datasets_meta_ok_pct())

    def test_full_datasets_meta_ok_pct(self):
        self.assertEqual(1.0, self.gen_full_data.datasets_meta_ok_pct())

    def test_empty_datasets_meta_ok_pct(self):
        self.assertEqual(None, self.gen_empty.datasets_meta_ok_pct())

    def test_just_datasets_con_datos_cant(self):
        self.assertEqual(16, self.gen_justicia.datasets_con_datos_cant())

    def test_full_datasets_con_datos_cant(self):
        self.assertEqual(1, self.gen_full_data.datasets_con_datos_cant())

    def test_empty_datasets_con_datos_cant(self):
        self.assertEqual(0, self.gen_empty.datasets_con_datos_cant())

    def test_just_datasets_sin_datos_cant(self):
        self.assertEqual(0, self.gen_justicia.datasets_sin_datos_cant())

    def test_full_datasets_sin_datos_cant(self):
        self.assertEqual(1, self.gen_full_data.datasets_sin_datos_cant())

    def test_empty_datasets_sin_datos_cant(self):
        self.assertEqual(0, self.gen_empty.datasets_sin_datos_cant())

    def test_just_datasets_con_datos_pct(self):
        self.assertEqual(1, self.gen_justicia.datasets_con_datos_pct())

    def test_full_datasets_con_datos_pct(self):
        self.assertEqual(0.5, self.gen_full_data.datasets_con_datos_pct())

    def test_empty_datasets_con_datos_pct(self):
        self.assertEqual(None, self.gen_empty.datasets_con_datos_pct())

    @requests_mock.Mocker()
    def test_just_distribuciones_download_url_ok_cant(self, req_mock):
        req_mock.head(requests_mock.ANY, text='resp')
        self.assertEqual(
            56, self.gen_justicia.distribuciones_download_url_ok_cant())

    @requests_mock.Mocker()
    def test_full_distribuciones_download_url_ok_cant(self, req_mock):
        req_mock.head(re.compile('/convocatorias-abiertas-anio-2015.pdf'),
                      status_code=404)
        req_mock.head(re.compile('/convocatorias-abiertas-anio-2015.csv'),
                      status_code=200)
        self.assertEqual(
            1, self.gen_full_data.distribuciones_download_url_ok_cant())

    def test_empty_distribuciones_download_url_ok_cant(self):
        self.assertEqual(
            0, self.gen_empty.distribuciones_download_url_ok_cant())

    @requests_mock.Mocker()
    def test_just_distribuciones_download_url_error_cant(self, req_mock):
        req_mock.head(requests_mock.ANY, text='resp')
        self.assertEqual(
            0, self.gen_justicia.distribuciones_download_url_error_cant())

    @requests_mock.Mocker()
    def test_full_distribuciones_download_url_error_cant(self, req_mock):
        req_mock.head(re.compile('/convocatorias-abiertas-anio-2015.pdf'),
                      status_code=404)
        req_mock.head(re.compile('/convocatorias-abiertas-anio-2015.csv'),
                      status_code=200)
        self.assertEqual(
            1, self.gen_full_data.distribuciones_download_url_error_cant())

    def test_empty_distribuciones_download_url_error_cant(self):
        self.assertEqual(
            0, self.gen_empty.distribuciones_download_url_error_cant())

    @requests_mock.Mocker()
    def test_just_distribuciones_download_url_ok_pct(self, req_mock):
        req_mock.head(requests_mock.ANY, text='resp')
        self.assertEqual(
            1, self.gen_justicia.distribuciones_download_url_ok_pct())

    @requests_mock.Mocker()
    def test_full_distribuciones_download_url_ok_pct(self, req_mock):
        req_mock.head(re.compile('/convocatorias-abiertas-anio-2015.pdf'),
                      status_code=404)
        req_mock.head(re.compile('/convocatorias-abiertas-anio-2015.csv'),
                      status_code=200)
        self.assertEqual(
            0.5, self.gen_full_data.distribuciones_download_url_ok_pct())

    def test_empty_distribuciones_download_url_ok_pct(self):
        self.assertEqual(
            None, self.gen_empty.distribuciones_download_url_ok_pct())

    @requests_mock.Mocker()
    def test_check_url_default_timeout(self, req_mock):
        req_mock.head(requests_mock.ANY, text='resp')
        self.gen_justicia.distribuciones_download_url_ok_pct()
        for request in req_mock.request_history:
            self.assertEqual(1, request.timeout)

    @requests_mock.Mocker()
    def test_check_url_override_timeout(self, req_mock):
        generator = StatusIndicatorsGenerator(
            self.get_sample('catalogo_justicia.json'), url_check_timeout=10)
        req_mock.head(requests_mock.ANY, text='resp')
        generator.distribuciones_download_url_ok_pct()
        for request in req_mock.request_history:
            self.assertEqual(10, request.timeout)
